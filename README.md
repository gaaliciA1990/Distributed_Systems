# Distributed_Systems
Homework projects for distributes systems class
</br>**Libraries**: Socket, Sys, Pickled
</br>
**Language**: Python3
## Lab 1 - Simple Client
A simple client that connect to a Group Coordinator Daemon (GCD). The GCD responds
with a list of potential group members which my client will send a message to. 
The responses are printed out and then exits the server.


## Lab 2 - Bully Algorithm
The bully algorithm expands on lab 1. The client connects to the GCD and talks to 
the GCD members to determine who is the leader. The leader is determined by the 
member with the fewest days till their birthday or, if the birthday is the same, 
the one with the smalled SU ID (int). The process listens for other members who want
to send messages to it. If ELECTION message is received, the higher process sends
this message to higher process's, and receives a dictionary of all group members, 
keyed listen_address with values of corresponding process_ids. An election is 
started to determine who is the leader. Once the leader is determined, the leader 
sends a COORDINATOR message stating they are the winner. 
