"""
CPSC 5520, Seattle University
Author: Alicia Garcia
Version: 1.0
"""
import sys


# noinspection PyMethodMayBeStatic
class Arbitrage:
    def __init__(self, prices):
        self.price_list = []
        self.graph = {}
        self.price_list = prices

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
        dist = {}
        pred = {}
        for node in graph:
            dist[node] = float('Inf')  # We set our edges to infinity to start
            pred[node] = None
        dist[source] = 0  # For the source we know how to reach, set dist to 0
        return dist, pred

    def bellman_ford(self, graph, source, tolerance):
        """
        This is supposed to run the bellman ford algorithm, modified to detect market arbitrage.
        The edges are relaxs and the negative cycle detection is called to determine if one
        exists for the updated graph
        :param graph: our graph holding the currencies nodes and price edges/weights
        :param source: the starting point for determining arbitrage in the graph
        :param tolerance: the threshold value for determine if we actually have a profit
        :return: the path of the potential arbitrage, else None
        """
        dist, pred = self.initialize(graph, source)

        for node in range(len(graph) - 1):
            for start_currency in graph:
                for end_currency in graph[start_currency]:
                    self.relax(start_currency, end_currency, graph, dist, pred, tolerance)

        # detect the arbitrage
        for start_currency in graph:
            for end_currency in graph[start_currency]:
                price_wt = graph[start_currency][end_currency]
                if dist[start_currency] is not float('Inf') and dist[end_currency] > dist[start_currency] + price_wt \
                        + tolerance:
                    return self.negative_cycle_detection(pred, source)
        return None

    def relax(self, start, neighbor, graph, dist, pred, tolerance):
        """
        Update the distance value by relaxing the edges
        :param start: node for currency A
        :param neighbor: node for currency B
        :param graph: our graph with all currencies and their rates
        :param dist: the next node in the graph
        :param pred: the previous node in the graph
        :param tolerance: the threshold for storing a negative value
        :return:
        """
        price_wt = graph[start][neighbor]

        if dist[neighbor] is not float('Inf') and dist[start] + price_wt + tolerance < dist[neighbor]:
            dist[neighbor] = dist[start] + price_wt
            pred[neighbor] = start

    def negative_cycle_detection(self, pred, start) -> list:
        """
        For found arbitrage, this method will trace back up the graph and return the path
        :param pred: predecessor node
        :param start: starting node for arbitrage detection
        :return: the loop for the arbitrage
        """
        arbitrage_loop = [start]
        next_node = start
        while True:
            try:
                next_node = pred[next_node]
                if next_node not in arbitrage_loop:
                    arbitrage_loop.append(next_node)
                else:
                    arbitrage_loop.append(next_node)
                    arbitrage_loop = arbitrage_loop[arbitrage_loop.index(next_node):]
                    return arbitrage_loop
            except KeyError as kerr:
                print('Key Error encountered: {}'.format(kerr))
                sys.exit(1)
