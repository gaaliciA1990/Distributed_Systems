"""
CPSC 5520, Seattle University
Author: Alicia Garcia
Version: 1.0
"""
import math


class Arbitrage:
    def __init__(self, dataList):
        self.price_list = []
        self.graph = {}
        self.price_list = dataList

    def build_graph(self) -> dict:
        """
        Build our graph based on the currencies and price we have stored in the list
        :return: the filled in graph
        """
        for key in self.price_list:
            conversion_rate = key[1]
            curr_a = key[0][0]
            curr_b = key[0][1]
            if curr_a != curr_b:
                if curr_a not in self.graph:
                    self.graph[curr_a] = {}
                self.graph[curr_a][curr_b] = float(conversion_rate)
        return self.graph

    def initialize(self, graph, source) -> tuple:
        """
        Initializes our graph by setting destiniation edge nodes to infinity.
        :param graph: the build graph with our currencies
        :param source: The starting point in the graph
        :return: the destination node and the predecessor node
        """
        dest = {}
        pred = {}
        for node in graph:
            dest[node] = float('Inf')  # We set our edges to infinity to start
            pred[node] = None
        dest[source] = 0  # For the source we know how to reach
        return dest, pred

    def relax(self, curr_a, curr_b, graph, dest, pred):
        """
        Set our price to the lowest price, if applicable
        :param curr_a:
        :param curr_b:
        :param graph:
        :param dest:
        :param pred:
        :return:
        """
        # Check if our destination is a leaf node

        # If the price between curr_a and curr_b is less than my current price
        # I want to record the lower price
        if dest[curr_b] > dest[curr_a] + graph[curr_a][curr_b]:
            dest[curr_b] = dest[curr_a] + graph[curr_a][curr_b]
            pred[curr_b] = curr_a

    def retrace_found_arbitrage(self, pred, start) -> list:
        """
        For found arbitrage, this method will trace back up the graph and
        :param pred:
        :param start:
        :return:
        """
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
        arbitrage_threshold = 1e-7  # set our tolerance threshold to avoid getting back same amount

        dest, pred = self.initialize(graph, source)
        for node in range(len(graph) - 1):
            for curr_a in graph:
                for curr_b in graph[curr_a]:  # For each neighbor of curr_a
                    self.relax(curr_a, curr_b, graph, dest, pred)

        # detect the arbitrage
        for curr_a in graph:
            for curr_b in graph[curr_a]:
                result = dest[curr_a] + graph[curr_a][curr_b]
                # is the difference between the value greater than our threshold
                if result - dest[curr_b] > arbitrage_threshold:
                    return self.retrace_found_arbitrage(pred, source)
        return None
