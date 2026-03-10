from abc import ABC, abstractmethod
from module1 import *
import pandas as pd

# abstract classes so this can be used to make graphs not about gene ontology specifically
class Graph(ABC):
    @abstractmethod
    def new_node(self, term):
        pass

    @abstractmethod
    def new_edge(self, relationship):
        pass

    @abstractmethod
    def get_parents(self):
        pass

    @abstractmethod
    def get_children(self):
        pass

class Node(ABC):
    @abstractmethod
    def get_info(self):
        pass

class Edge(ABC):
    @abstractmethod
    def get_info(self):
        pass


class GONode(Node):
    def __init__(self, go_id: str, name: str, namespace: str, defi: str, is_obsolete: bool = False, alt_ids : list = [], subsets: list = [], synonyms: list = [], consider : list = [], replaced_by : str = None):
        self._go_id = go_id
        self._name = name
        self._defi = defi
        if namespace not in ('biological_process', 'molecular_function', 'cellular_component'):     # check if spelling is the same as GO file
            raise ValueError('Invalid namespace')
        else:
            self._namespace = namespace
        self._is_obsolete = is_obsolete
        self._alt_ids = alt_ids
        self._subsets = subsets
        self._synonyms = synonyms
        self._consider = consider
        self._replaced_by = replaced_by

    def get_info(self):
        s = f'Gene Ontology term with id {self._go_id}:\n\t{self._name} belonging to namespace {self._namespace}\n\t{self._defi}'
        return s
    
    @property
    def go_id(self):
        return self._go_id
    @property
    def name(self):
        return self._name
    @property
    def namespace(self):
        return self._namespace
    @property
    def is_obsolete(self):
        return self._is_obsolete
    @property
    def alt_ids(self):
        return self._alt_ids
    @property
    def subsets(self):
        return self._subsets
    @property
    def synonyms(self):
        return self._synonyms
    @property
    def consider(self):
        return self._consider
    @property
    def replaced_by(self):
        return self._replaced_by
    

    

class GOEdge(Edge):
    def __init__(self, child: GONode, parent: GONode, rtype: str):
        if not (isinstance(child,GONode) and isinstance(parent,GONode)):       
            raise TypeError('The edge connects two objects which are not both GO nodes.')
        else:
            self._child = child
            self._parent = parent
            self._rtype = rtype
    
    def get_info(self) -> str:
        return f'{self._child.name} (id: {self._child.go_id}) {self._rtype} {self._parent.name} (id: {self._parent.go_id})'
    
    @property
    def child(self):
        return self._child
    @property
    def parent(self):
        return self._parent
    @property
    def rtype(self):
        return self._rtype
    



class OntologyGraph(Graph):
    def __init__(self, annotations_df: pd.DataFrame):
        self.__nodes = dict()		# key = go_id (string), value = GONode object corresponding to that go_id
        self.__edges = dict()		# key = child.go_id, value = GOEdge object of that child GO term
        self.__annotations = annotations_df
    
    def new_node(self, term: GONode):
        self.__nodes[term.go_id] = term
        self.__edges[term.go_id] = list()
    
    def new_edge(self, relationship: GOEdge):
        term = relationship.child.go_id
        self.__edges[term].append(relationship)     
    
    def get_parents(self, node: GONode, edge: bool = True) -> list:       # this returns the list of GOEdge objects where node is the child
        # node can be a GONode or a string with the go_id, in the first case we extract the go_id:
        if isinstance(node, GONode):
            go_id = node.go_id
        try:
            parents = self.__edges[go_id]
            
            if edge:	# if edge is True we return a list of GOEdge where node is the child
                return parents
            else:		# if edge is False we return a list of GONodes parents of node
                return [e.parent for e in parents]
        except:
            return None
    
    def get_children(self, node, edge: bool = True) -> list:     # this returns the list of GOEdge objects / children GONode where node is the parent
        # node can be a GONode or a string with the go_id, in the first case we extract the go_id:
        if isinstance(node, GONode):
            go_id = node.go_id
        try:    
            children = list()
            for n in self.get_nodes_ids():
                for edge in self.__edges[n]:
                    if edge.parent.go_id == go_id:
                        children.append(edge)
            
            if edge:# if edge is True, we just return the GOEdge
                return children
            else:	# else, we only return the GONode objects of children
                return [e.child for e in children]
        except:
            return None

    def get_nodes(self) -> dict:		# returns a dictionary where the key is the term go_id and the value is the GONode object related
        return self.__nodes.copy()
    
    def get_GONodes(self) -> list:		# this returns a list of GONode objects, without the key
        return list(self.__nodes.values())
    
    def get_nodes_ids(self) -> list:
        return list(self.__nodes.keys())
    
    def get_node(self, go_id: str) -> GONode:
        return self.__nodes[go_id]
    

    
def create_graph(dataframes: DataBundle) -> OntologyGraph:        # the function to call to create the graph
    
    def create_node(row):
        node = GONode(row["go_id"], row["name"], row["namespace"], row["definition"], row["is_obsolete"], row["alt_ids"],
                      row["subsets"], row["synonyms"], row["consider"], row["replaced_by"]) 
        graph.new_node(node)
    
    def create_edge(row):
        child = graph.get_node(row["child_id"])
        parent = graph.get_node(row["parent_id"])
        rel = GOEdge(child, parent, row["relation"])
        graph.new_edge(rel)
        
        
    graph = OntologyGraph(dataframes.annotations_df)
    dataframes.terms_df.apply(create_node, axis=1)
    dataframes.edges_df.apply(create_edge, axis=1)
    
    return graph
