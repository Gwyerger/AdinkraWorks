# Given a set of L matrices, format the Adinkra object
import os
import numpy as np
from icecream import ic
import ast

def string_to_nested_list(string_representation):
    """
    Converts a string representation of a nested list to an actual nested list.

    Args:
        string_representation: The string to convert.

    Returns:
        A nested list.
    """
    try:
        return ast.literal_eval(string_representation)
    except (SyntaxError, ValueError):
        return "Invalid string format for nested list"


# Adinkra class
class Adinkra:
    def __init__(self, path : str):
        if os.path.exists(os.path.join(path)):
            self.path = path
            # For Table (assuming space-separated)
            with open(self.path, "r") as file:
                text = file.readlines()
            for line in text:
                line= line.replace("}", "]").replace("{", "[").replace("\n", "").replace("\"", "").replace("\'", "")
                list = string_to_nested_list(line)
                Ls = np.array(list[0])
                num_colors = Ls.shape[0]
                num_bosons = Ls.shape[1]
                num_fermions = Ls.shape[2]
                self.boson_elevations = np.zeros(num_bosons)
                self.fermion_elevations = np.ones(num_fermions)
                # Create a list of colored edges of the form [*colors: [*connections [*boson, *fermion, *dashing: +/-1]]...]
                edges = np.array([[[j, np.nonzero(Ls[i,j])[0][0], Ls[i,j,np.nonzero(Ls[i,j])[0][0]]] for j in range(num_bosons)] for i in range(num_colors)])
                self.adinkra_colors = num_colors
                self.adinkra_size = (num_bosons, num_fermions)
                self.edges = edges[:, :, 0:2]
                self.dashing = edges[:, :, 2]
        else:
            print(f"File {path} does not exist.")
    def __repr__(self):
        return f"Adinkra ({self.adinkra_size[0]}x{self.adinkra_size[1]}) at path: {self.path}\nBoson elevations: {self.boson_elevations}\nFermion elevations: {self.fermion_elevations}" 


# Example Export from Mathematica: 
# Export["/home/gabriel/python_projects/AdinkraWorks/tests/SMw1.csv", {{{Ls, Rs}}}, "CSV"]

# Example Import
a = Adinkra("/home/gabriel/python_projects/AdinkraWorks/tests/SMw1.csv")
print(a)

