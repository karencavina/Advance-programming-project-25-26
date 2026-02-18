from graph import *
import module1 as m1

#groups nodes by namespace type
def groupBy(g: OntologyGraph, argument:str):
    return [node for node in g.get_nodes() if node.namespace == argument]

#returns the path between nodes as list of nodes
#search is Depth first and returns shortest path
def pathFinder(g: OntologyGraph, n1: GONode, n2: GONode, path: list = None, shortest: list = None):
    if path == None:
        path = list()
    path.append(n1)
    if n1 == n2:
        return path
    for n in g.get_out(n1):
        if shortest == None or len(path) < len(shortest):
            newPath = pathFinder(g,n,n2,path,shortest)
            if newPath != None:
                shortest = newPath
    return shortest

# given the path between two nodes returns it's lenght
def pathLenght(g: OntologyGraph, n1: GONode, n2: GONode):
    p = pathFinder(g,n1,n2)
    if p == None:
        print(f"No path between the nodes {n1.id} and {n2.id} exists")
    else:
        return len(p)

# returns the number of child nodes of a given node
def childsNumber(g: OntologyGraph, n: GONode):
    return len(getChilds(g,n))

# same as childsNumber but for parent nodes
def parentsNumber(g: OntologyGraph, n: GONode):
    return len(getParents(g,n))

# returns the number of edges a node has, makes no distinction between edges going in and out, that is the job of child/parentsNumber
def edgesNumber(g: OntologyGraph, n:GONode):
    return (childsNumber(g,n) + parentsNumber(g,n))

# returns a list of all the nighbours ids of a given node 
def getNeighbours(g: OntologyGraph, n:GONode):
    out = list()
    for e in g.get_in(n):
        out.append(e.start.id())
    for e in g.get_out(n):
        if e.end().id() not in out:
            out.append(e.end().id())
    return out

# returns a list of edges connecting a given node to it's neighbours
def getNeighboursEdges(g:OntologyGraph, n:GONode):
    out = list()
    nodes = getNeighbours(g,n)
    edges = g.get_edges()
    for node in nodes:
        for edge in edges:
            if (n == edge.start() and node == edge.end()) or (n == edge.end() and node == edge.start()):
                out.append((node.id(),edge.rtype()))
    return out
    
# given a node of the graph returns all the child nodes ids as a list
def getChilds(g: OntologyGraph, n: GONode):
    return [e.start.id() for e in g.get_in(n)]

# same as get childs but for parents
def getParents(g: OntologyGraph, n: GONode):
    return [e.end.id() for e in g.get_out(n)]

# returns a list of ids of neighbours of a given node based on the relation type
def getNeighboursByRType(g:OntologyGraph, n: GONode, RType:str):
    out = list()
    edges = getNeighboursEdges(g,n)
    for edge in edges:
        if edge.rtype() == RType:
            if n == edge.start():
                out.append(edge.end().id())
            else:
                out.append(edge.start().id())
    return out

# returns a list of synonims of a given id
def getIdSynonims(g: OntologyGraph,id: int):
    return None