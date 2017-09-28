import numpy as np
from os.path import isfile
from emmail.objects.resultRow import ResultRow, EmmImposters
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

### Implement functions to use these headers.
short_header = "Isolate\tNumberOfClusters\tAnswers\tSuspectImposters\n"
verbose_header = "Isolate\tNumberOfHits\tNumberOfClusters\tAnswers\tAnswerPositions\tSuspectImposters\tSuspectPositions\n"

nullResult = ResultRow("0\tEMM0.0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0") 

class Clusterer:
    def __init__(self, blastOutputFile, output_stream, verbose=False, distance=500, linkage="ward", header=True):
        self.isolate = blastOutputFile
        self.results = self.extractFromFile(blastOutputFile)
        self.header = header
        
        self.output_stream = output_stream
        self.verbose = verbose
        
        self.clust_distance = distance
        self.linkage = linkage
        
        self.cluster_number = 0
        self.ascii_vis = self.isolate
    
    def __repr__(self):
        string = ("Clusterer for {} with binwidth {}bp, resulting in {} cluster(s)\n{} output to {}")
        
        return string.format(self.isolate, self.clust_distance, self.cluster_number,
                            "Verbose" if self.verbose else "Short", self.output_stream)
    
    def extractFromFile(self, blastOutputFile):
        with open(blastOutputFile, "r") as handle:
            results = [ResultRow(line.strip()) for line in handle.readlines()]
            
        return results
    
    def list_to_string(self, answers):
        string = ""
        logger.debug("There are {} answers".format(len(answers)))
        
        for answer in answers:
            if type(answer) is ResultRow:
                string += str(answer)
            elif type(answer) is list:
                positions = set([ans.queryStart for ans in answer])
                for pos in positions:
                    string += "({})".format(";".join([str(ans) for ans in answer if ans.queryStart == pos]))
            else:
                raise Exception("answer is {}".format(type(answer)))
            
            string += ";"
            
        return string[:-1]
    
    def short_stringer(self):
        header = "Isolate\tNumberOfClusters\tAnswers\tSuspectImposters\n"
        string = "{0}\t{1}\t{2}\t{3}".format(
                            self.isolate,
                            self.cluster_number,
                            self.list_to_string(self.answers),
                            self.list_to_string(self.possible_imposters))

        string = short_header + string if self.header else string
        return string
    
    def verbose_stringer(self):
        header = "Isolate\tNumberOfHits\tNumberOfClusters\tAnswers\tAnswerPositions\tSuspectImposters\tSuspectPositions\n"
        string = "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}".format(
                                        self.isolate, 
                                        len(self.results), 
                                        self.cluster_number, 
                                        self.list_to_string(self.answers),
                                        ";".join(["{}:{}".format(answer.contig, answer.queryStart) for answer in self.answers]),
                                        self.list_to_string(self.possible_imposters),
                                        ";".join(["{}:{}".format(x.contig, x.queryStart) for x in self.possible_imposters
                                                    if x.score >= 92]))
        
        string = verbose_header + string if self.header else string
        return string
    
    def visualize_contig(self, contig):
        ### EXPERIMENTAL
        # Visual map of emm hits within WGS
        
        def determine_position(result):
            if type(result) is ResultRow:
                return result.queryStart
            elif type(result) is list:
                return sum([p.queryStart for p in result])/len(result)
            else:
                raise Exception("Something is wrong in visContig")
                
        contig = [result[1] for result in contig]
        string = ""
        
        for j, pos in enumerate(contig): # List of results with best score in cluster
            hit = str(pos)
            position = determine_position(pos)
            
            if j == 0:
                string += hit
            else:
                distance = int((position - prevPos) // self.clust_distance)
                if distance < 0:
                    string = "{}{}{}".format(hit, "-" * abs(distance), string)
                else:
                    string = "{}{}{}".format(string, "-" * abs(distance), hit)
            
            prevPos = position
            
        return string   
    
    def cluster(self, results):
        """
        Cluster a list of results.
        """
        if len(results) == 1:
            return [1]
        
        elif len(results) >= 2:
            positions = [result.positions for result in results]
            Z = linkage(positions, self.linkage)
            clusters = fcluster(Z, self.clust_distance, criterion="distance")
            
            return clusters
        
        else:
            raise Exception("Cannot run with {} results.".format(len(positions)))
            
    def get_best_scoring(self, results):
        """
        Returns the best scoring result, or results when there are multiple 100-scoring results.
        """
        if len(results) > 0:
            maxScore = max([result.score for result in results])
            maxResult = [result for result in results if result.score == maxScore]
            
            if len(maxResult) == 1:
                return maxResult[0]
            else:
                if (set([result.score for result in maxResult])) == set([100]):
                    return maxResult
                else:
                    # If scores are not 100, take random result from the array
                    pos = np.random.randint(len(maxResult), size=1)[0]
                    return maxResult[pos]
            
        else:
            # When there is no result, return a null ResultRow object.
            return nullResult      
    
    def best_in_cluster_in_contig(self, contig):
        """
        Take an integer value representing the contig, and return best-scoring result(s) in every cluster within the contig.
        """
        
        # Extract results that fall within contig and cluster them together
        within_contig = np.array([result for result in self.results if result.positions[0] == contig])
        contig_cluster = self.cluster(within_contig)
        
        # Look for best-scoring within each cluster and return as a list of best results in contig.
        if len(within_contig) == 1:
            return [(1, within_contig[0])]
        
        elif len(within_contig) > 1:
            answer = []

            for cluster in set(contig_cluster):           
                within_cluster = within_contig[contig_cluster == cluster]
                answer.append((len(within_cluster), self.get_best_scoring(within_cluster)))
        
        else:
            raise Exception("Cannot run with {} results".format(len(within_contig)))
        
        return answer
        
    def classify_expected_answer(self, max_iteration=10):
        
        def is_in(all_votes, answers):
            """
            Find whether objects within a bigger list is in a smaller list,
            return boolean values to be used in numpy array indexing.
            """
            bools = np.zeros(len(all_votes), dtype=bool)
            
            for index, vote in enumerate(all_votes):
                logger.debug("is {} in answers? {}".format(vote, vote in answers))
                bools[index] = 1 if vote in answers else 0
            
            logger.debug("is_in() returns {}".format(bools))
            return bools
        
        def process_answer_logic(voted_result):
            """
            To use when imposters filter is still used.
            
            Take heed that the list of voted results can have objects in the form of ResultRow or list,
            list being there if ResultRow in the list all are 100-scoring.
            
            Consider results that follow along the arguments:
            If there is only 1 object or list, return if it is not imposter.
            If there are more than 1 object or list, return the best scoring that is not imposter.
            """
            
            if voted_result.shape[0] == 1:
                # If there is only one, it is okay as long as it is not EmmImposters
                logger.debug("Voted result is singular")
                
                tmp_result = voted_result[0]
                answer = []
                if type(tmp_result) == ResultRow:
                    answer += [tmp_result] if (tmp_result.type not in EmmImposters) else []
                elif type(tmp_result) == list:
                    # Make sure all in the list is not imposters, add as answer if all within the list follows if argument
                    tmp_answer = [result for result in tmp_result
                                 if (result.type not in EmmImposters)] 
                    answer += [tmp_answer] if len(tmp_answer) == len(tmp_result) else []

            elif voted_result.shape[0] > 1:
                # If there is more than one, score would come into play
                logger.debug("Voted result is non-singular")
                
                tmp_result = voted_result
                max_score = max([result.score for result in tmp_result])
                answer = []
                for result in tmp_result:
                    answer += [result] if (result.type not in EmmImposters and result.score == max_score) else []
            
            return answer
        
        def process_answer_absurd(voted_result):
            """
            To use when imposters filter is still used.
            
            Take heed that the list of voted results can have objects in the form of ResultRow or list,
            list being there if ResultRow in the list all are 100-scoring.
            
            Consider results that follow along the arguments:
            If there is only 1 object or list, return.
            If there are more than 1 object or list, return the best scoring.
            """
            
            if voted_result.shape[0] == 1:
                logger.debug("Voted result is singular")
                
                tmp_result = voted_result[0]
                answer = []
                if type(tmp_result) == ResultRow:
                    answer += [tmp_result]
                    
                elif type(tmp_result) == list:
                    # Make sure all in the list is not imposters
                    tmp_answer = [result for result in tmp_result] 
                    # Add as answer if all within the list follows if argument
                    answer += [tmp_answer] if len(tmp_answer) == len(tmp_result) else []

            elif voted_result.shape[0] > 1:
                logger.debug("Voted result is non-singular")
                
                tmp_result = voted_result
                max_score = max([result.score for result in tmp_result])
                answer = []
                for result in tmp_result:
                    answer += [result] if result.score == max_score else []
            
            return answer
        
        """
        Determine which cluster(s) is the best to return as answer,
        while returning the remaining clusters as possible imposters.
        """
        
        votes = np.array([[item[0], item[1]] for item in self.best_in_clusters])
        votes_sorted = sorted(set(votes[:,0]), reverse=True)
        logical_result = []

        while logical_result == [] and len(votes_sorted) > 0:
            voted_result = votes[votes[:, 0] == votes_sorted.pop(0), 1]
            logical_result = process_answer_logic(voted_result)
            
            logger.debug("Votes remaining = {}".format(len(votes_sorted)))
        
        if logical_result == []:
            logger.debug("Move to ignore emm-like filter")
            
            votes = np.array([[item[0], item[1]] for item in self.best_in_clusters])
            votes_sorted = sorted(set(votes[:,0]), reverse=True)
            
            while logical_result == [] and len(votes_sorted) > 0:
                voted_result = votes[votes[:, 0] == votes_sorted.pop(0), 1]
                logical_result = process_answer_absurd(voted_result)
                
                logger.debug("Votes remaining = {}".format(len(votes_sorted)))
            
            logger.debug("This is illogical, but answer is = {}".format(logical_result))
            
        logger.debug("The answer would be {}".format(logical_result))
        
        self.answers = logical_result
        self.possible_imposters = votes[~is_in(votes[:,1], self.answers), 1] 
    
    def main(self):
        if len(self.results) > 0:
            self.best_in_clusters = []

            for i in set([result.positions[0] for result in self.results]): # For every contig
                contig_best = self.best_in_cluster_in_contig(i)
                
                self.best_in_clusters.extend(contig_best)
                
                self.cluster_number += len(contig_best)
                self.ascii_vis += "\t" + self.visualize_contig(contig_best)
            
            # Now get final answer
            self.classify_expected_answer()
        
        else:
            self.answers = [nullResult]
            self.possible_imposters = [nullResult]
                    
        final_result =  self.verbose_stringer() if self.verbose else self.short_stringer()
        
        if self.output_stream in [None, "None", "stdout"]:
            print(final_result)
        else:         
            with open(self.output_stream, "a") as handle:
                handle.write(final_result+"\n")
        
        return final_result