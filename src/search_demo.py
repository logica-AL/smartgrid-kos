"""Synthetic BFS demonstration; the graph is illustrative, not sensor data."""
from collections import deque
import json
from pathlib import Path

GRAPH={"Lobi":["Koridor A","Koridor B"],"Koridor A":["Lobi","Kamar 1","Kamar 2"],"Koridor B":["Lobi","Kamar 3"],
       "Kamar 1":["Koridor A"],"Kamar 2":["Koridor A"],"Kamar 3":["Koridor B"]}

def bfs(graph,start,goal):
    q=deque([start]); parent={start:None}; explored=[]
    while q:
        node=q.popleft(); explored.append(node)
        if node==goal:
            path=[]; cur=node
            while cur is not None: path.append(cur); cur=parent[cur]
            return path[::-1],explored
        for nxt in graph.get(node,[]):
            if nxt not in parent: parent[nxt]=node; q.append(nxt)
    return None,explored

def main():
    path,explored=bfs(GRAPH,"Lobi","Kamar 2")
    result={"source":"synthetic illustrative corridor graph, not real sensor data","state":"technician current node","action":"move to adjacent node","goal":"Kamar 2 alert","cost":"1 per edge; all edges equal","graph":GRAPH,"path":path,"explored_nodes":explored,"explored_count":len(explored),"complete":"yes for reachable goal in a finite graph","optimal":"shortest edge-count path for an unweighted graph","complexity":{"time":"O(V+E)","space":"O(V)"},"weighted_graph_note":"For unequal edge costs, use Dijkstra or A*."}
    out=Path("outputs/bfs_result.json"); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(result,ensure_ascii=False))

if __name__=="__main__": main()
