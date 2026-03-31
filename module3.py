from graph import *
import module1 as m1

class Analysis():

    def __init__(self,g:OntologyGraph):
        self.__graph = g

    @property
    def get_Graph(self):
        return self.__graph
    

    #groups nodes by namespace type
    def group_By(self, argument:str) -> list:
        return [node for node in self.__graph.get_GONodes() if node.namespace() == argument]

    #returns the path between nodes as list of nodes
    #search is Depth first and returns shortest path
    def path_Try(self, n1: GONode, n2: GONode, path: list = None, shortest: list = None) -> list:
        if path == None:
            path = []
        path = path + [n1]
        if n1 == n2:
            return path
        #for n in g.get_parents(n1,True):
        '''
        uno deve poter scegliere il verso della ricerca
        '''
        for n in self.__graph.get_parents(n1, False):
            if n in path:
                continue
            if shortest == None or len(path) < len(shortest):
                newPath = self.path_Try(n,n2,path,shortest)
                if newPath != None and (shortest==None or len(shortest) > len(newPath)):
                    shortest = newPath
        return shortest

    def path_Finder(self, n1: GONode, n2: GONode) -> list:
        a = self.path_Try(n1,n2)
        b = self.path_Try(n2,n1)
        if a == None:
            return b
        elif b == None:
            return a
        elif len(a) <= len(b):
            return a
        else:
            return b

    # returns a list of all the nighbours of a given node 
    def get_Neighbours(self, n:GONode) -> list:
        out = []
        for e in self.__graph.get_parents(n,False):
            out.append(e)
        for e in self.__graph.get_children(n,False):
            out.append(e)
        return out



    def get_Similarity(self, n1: GONode, n2:GONode) -> float:
        '''
        returns a percentage of the similarity of two GOnodes using the Dice-Sørensen coefficient
        0 means two nodes are completely different, 1 means they are the same node
        the formula is 2*the intersection of the nodes (how many property they share) divided by the number of property of n1 + the number of property of n2
        ignores obsolete,
        if two nodes have the same id returns 1 by default
        '''
        n1N2Prop = 18 # number of n1+n2 properties starts from the max and reduces if any arent present
        overlap = 0

        def propertyCompareStr(self, p1:str, p2:str) -> float:
            '''
            given the property of the two nodes compares them by increasing eq by 1 for every word contained in both
            and returns eq over the length of the longest in term of words of the two properties.
            '''
            if p1 == None or p2 == None:
                n1N2Prop -= 2
                return 0

            eq = 0
            p1 = p1.split(" ")
            p2 = p2.split(" ")

            for w in p1:
                if len(w) <= 3:
                    p1.remove(w)
                    p2.remove(w)
                elif w in p2:
                    eq += 1
            if len(p1) > len(p2):
                return eq/len(p1)
            else:
                return eq/len(p2)

        def propertyCompareList(self, p1:list, p2:list):
            '''
            same propertyCompareStr but works for properties that are stored as lists
            '''
            if p1 == None or p2 == None:
                n1N2Prop -= 2
                return 0

            eq = 0
            for w in p1:
                if w in p2:
                    eq += 1
            if len(p1) > len(p2):
                return eq/len(p1)
            else:
                return eq/len(p2)

        def propertyCompareId(self, p1:list,p2:list):
            ''' 
            some properties are saved as lists of ids in particular synonyms and consider 
            this function compares them taking into account the possibility of one node's Id being present in the other
            better said, there is difference between having a common synonym and one being the synonym of the other
            '''
            if p1 == None or p2 == None:
                n1N2Prop -= 2
                return 0

            eq = 0
            for w in p1:
                if w in p2:
                    eq += 2
                if w == n2.go_id:
                    eq += 4 # we count as "more impactfull" if their own ids are in the list
            return eq(len(p1) + len(p2))

        if n1.go_id == n2.go_id or n1.replaced_by == n2.go_id or n2.replaced_by == n1.go_id: # in theese three cases the nodes are either the same or one replaces the other se we just return 1
            return 1
        else:
            if n1.namespace == n2.namespace: # there are only three possible namespaces so it's enough to check if they are the same or not
                overlap += 1

            overlap += propertyCompareStr(n1.name, n2.name)
            overlap += propertyCompareStr(n1.defi,n2.dedi)
            overlap += propertyCompareList(n1.subsets,n2.subsets)
            overlap += propertyCompareList(n1.alt_ids,n2.alt_ids)
            overlap += propertyCompareId(n1.synonyms,n2.synonyms)
            overlap += propertyCompareId(n1.consider,n2.consider)

            return (overlap/n1N2Prop)
        
    def get_Statistics(self) -> dict:
        '''
        returns a dictionary with various statistics about the graph:
        - average number of edges per node
        - average number of synonyms
        '''
        ret = dict()

        #average number of synonyms per node
        avg_synonyms = 0
        for n in self.get_Graph.get_GONodes():
            avg_synonyms += len(n.synonyms)
        ret["avg_synonyms"] = avg_synonyms/len(self.get_Graph.get_GONodes())
        

        # average number of edges per node
        avg_edge = 0
        for n in self.get_Graph.get_GONodes():
            avg_edge += len(self.get_Graph.get_children(n))
            avg_edge += len(self.get_Graph.get_parents(n))
        ret["avg_edges"] = avg_edge/len(self.get_Graph.get_GONodes)


        #average number of alternative ids per node
        avg_alt_ids = 0
        for n in self.get_Graph.get_GONodes():
            ret += len(n.alt_ids())
        ret["avg_alt_ids"] = avg_alt_ids/len(self.get_Graph.get_GONodes())
        

        #number of obsolete nodes
        obsolete_amount = 0
        for n in self.get_Graph.get_GONodes():
            if n.is_obsolete():
                obsolete_amount += 1
        ret["obsolete_amount"] = obsolete_amount
        

        # number of nodes considered by other nodes (if a node is considered multiple times it counts only once)
        considered_amount = set()
        for n in self.get_Graph.get_GONodes():
            for m in self.get_Graph.get_GONodes():
                if n.go_id() in m.consider():
                    considered_amount.add(n.go_id())
                    continue
        ret["considered_amount"] = len(considered_amount)


        # tuple of percentages of distribution of the three namespaces
        # the order is biological process, molecular function, cellular component
        bio = 0
        mol = 0
        cel = 0
        for n in self.get_Graph.get_GONodes():
            if n.namespace() == 'biological_process':
                bio += 1
            elif n.namespace() == 'molecular_function':
                mol += 1
            elif n.namespace() == 'cellular_component':
                cel += 1
        total = bio + mol + cel
        bio = (bio/total) * 100
        mol = (mol/total) * 100
        cel = (cel/total) * 100
        ret["namespaces_percentage"] = (bio,mol,cel)


        # average number of parents per node
        avg_parents = 0
        for n in self.get_Graph.get_GONodes():
            avg_parents += len(self.get_Graph.get_parents(n,False))
        ret["avg_parents"] = avg_parents/len(self.get_Graph.get_GONodes())


        # average number of children per node
        avg_children = 0
        for n in self.get_Graph.get_GONodes():
            avg_children += len(self.get_Graph.get_children(n,False))
        ret["avg_children"] = avg_children/len(self.get_Graph.get_GONodes)
        

        return ret