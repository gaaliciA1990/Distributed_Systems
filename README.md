# Distributed_Systems
Homework projects for distributes systems class
</br>**Libraries**: Socket, Sys, Pickled
</br>
**Language**: Python3
## Lab 1 - Simple Client
A simple client that connect to a Group Coordinator Daemon (GCD) utilizing TCP/IP connections. The GCD responds
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


## Lab 3 - Arbitrage Detection with Published Quote
The program implements the Bellman-Ford algorithm listens to currency exchange rates 
from a price feed and prints our a message whenever there's an arbitrage opportunity
available, utilizing UDC/IP connections. As of right now, the arbitrage appears to be 
detected in the reverse (showing losses instead of profit). I have exhausted all brain power
to fix it, but have not been able to identify what is wrong in my code.
