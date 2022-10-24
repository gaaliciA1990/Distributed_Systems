"""
CPSC 5520, Seattle University
Author: Alicia Garcia
Version: 1.0
"""


class Graph:
    def __init__(self, vertices):
        self.vertices = vertices
        self.graph = []

    def add_edge(self, currency_a, currency_b, weight):
        """
        Add a new edge to the graph
        :param currency_a: the currency node that starts the edge
        :param currency_b: the current node that ends the edge
        :param weight: forex trading market between the currency nodes
        :return:
        """
        self.graph.append([currency_a, currency_b, weight])

    def print_solution(self, exchange_rate):
        """
        Utility function to print the solution for exchange rate
        :param exchange_rate: forex trading market between two nodes (Currencies)
        :return:
        """
        for i in range(self.vertices):
            print("{0}\t\t{1}".format(i, exchange_rate[i]))

    def arbitrage(self, source):
        """
        Detects when an arbitrage can be executed by implementing bellman-ford's algorithm
        to use a negative weight cycle. If the edges (which are the cost of the trade) return
        a negative cycle, we know we have a profit opportunity, therefore arbitrage.
        :param source:
        :return:
        """
        # Initialize distances from source to all other vertices as Infinite
        exchange_rate = [float("Inf")] * self.vertices
        exchange_rate[source] = 0

        # The shortest path from the source to any other vertex can have at most vertices -1 edges
        for _ in range(self.vertices - 1):
            # update the exchange rate and parent index of the adjacent vertices of the picked vertex
            # consider only vertices still in the queue
            for currency_a, currency_b, weight in self.graph:
                if exchange_rate[currency_a] != float("Inf") and exchange_rate[currency_a] + weight < exchange_rate[
                    currency_b]:
                    exchange_rate[currency_b] = exchange_rate[currency_a] + weight

        # Check the negative weight cycle
        for currency_a, currency_b, weight in self.graph:
            if exchange_rate[currency_a] != float("Inf") and exchange_rate[currency_a] + weight < exchange_rate[
                currency_b]:
                print("ARBITRAGE:")
