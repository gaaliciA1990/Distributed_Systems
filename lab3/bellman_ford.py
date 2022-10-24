"""
CPSC 5520, Seattle University
Author: Alicia Garcia
Version: 1.0
"""
import math


class Arbitrage:
    def __init__(self):
        self.price_list = []
        self.graph = {}

    def add_price(self, currency_a, currency_b, price):
        """
        Add a new edge to the graph
        :param currency_a: the currency node that starts the edge
        :param currency_b: the current node that ends the edge
        :param price: forex trading market between the currency nodes
        """
        self.price_list.append([currency_a, currency_b, price])

    def build_graph(self) -> dict:
        """
        Build our graph based on the currencies and price we have stored in the list
        :return: the filled in graph
        """
        for key in self.price_list:
            conversion_rate = -math.log(float(key[2]))
            curr_a = key[0]
            curr_b = key[1]
            if curr_a != curr_b:
                if curr_a not in self.graph:
                    self.graph[curr_a] = {}
                self.graph[curr_a][curr_b] = float(conversion_rate)
        return self.graph

    def initialize(self, graph, source) -> tuple:
        dest = {}
        pred = {}
        for node in graph:
            dest[node] = float('Inf')  # We start admiting that the rest of nodes are very very far
            pred[node] = None
        dest[source] = 0  # For the source we know how to reach
        return dest, pred

    def relax(self, curr_a, curr_b, graph, dest, pred):
        # If the price between curr_a and curr_b is lower than my current price
        if dest[curr_b] > dest[curr_a] + graph[curr_a][curr_b]:
            # Record this lower price
            dest[curr_b] = dest[curr_a] + graph[curr_a][curr_b]
            pred[curr_b] = curr_a

    def retrace_negative_loop(self, pred, start) -> list:
        arbitrage_loop = [start]
        next_node = start
        while True:
            next_node = pred[next_node]
            if next_node not in arbitrage_loop:
                arbitrage_loop.append(next_node)
            else:
                arbitrage_loop.append(next_node)
                arbitrage_loop = arbitrage_loop[arbitrage_loop.index(next_node):]
                return arbitrage_loop

    def bellman_ford(self, graph, source):
        dest, pred = self.initialize(graph, source)
        for i in range(len(graph) - 1):  # Run this until is converges
            for curr_a in graph:
                for curr_b in graph[curr_a]:  # For each neighbour of u
                    self.relax(curr_a, curr_b, graph, dest, pred)  # Relax

        # Step 3: check for negative-weight cycles
        for curr_a in graph:
            for curr_b in graph[curr_a]:
                if dest[curr_b] < dest[curr_a] + graph[curr_a][curr_b]:
                    return self.retrace_negative_loop(pred, source)
        return None