#----------AdinkraWorks----------#
# Copyright (c) 2025 Gabriel W. Yerger
# Licensed under the MIT License - see LICENSE file for details
#
# Given a set of L matrices, format the Adinkra object
import os
import numpy as np
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
                print(Ls[3])
                num_colors = Ls.shape[0]
                num_bosons = Ls.shape[1]
                num_fermions = Ls.shape[2]
                self.boson_elevations = np.ones(num_bosons)
                self.fermion_elevations = np.zeros(num_fermions)
                # Create a list of colored edges of the form [*colors: [*connections [*boson, *fermion, *dashing: +/-1]]...]
                edges = np.array([[[j, np.nonzero(Ls[i,j])[0][0], Ls[i,j,np.nonzero(Ls[i,j])[0][0]]] for j in range(num_bosons)] for i in range(num_colors)])
                self.adinkra_colors = num_colors
                self.adinkra_size = (num_bosons, num_fermions)
                self.edges = edges[:, :, 0:2]
                self.dashing = edges[:, :, 2]
            self.boson_positions = None
            self.fermion_positions = None
            self.boson_labels = None
            self.fermion_labels = None
            self.edge_colors = None
        else:
            print(f"File {path} does not exist.")
    def __repr__(self):
        return f"Adinkra ({self.adinkra_size[0]}x{self.adinkra_size[1]}) at path: {self.path}\nBoson elevations: {self.boson_elevations}\nFermion elevations: {self.fermion_elevations}" 

import re 

def Adinkra_to_CSV(filepath, Ls, Rs):
    line = ['"',"{","{"]
    for i,L in enumerate(Ls):
        line.append("{")
        for j,row in enumerate(L.astype(np.int8)):
            s = str(row)
            s = s.strip("[]")                  # "  1  0 1"
            s = re.sub(r"\s+", ",", s)         # ",1,0,1"
            s = s.strip(",")                   # "1,0,1"
            s = "{" + s + "}"
            line.append(s)
            if j != len(L)-1:
                line.append(",")
        line.append("}")
        if i != len(Ls)-1:
            line.append(",")
    line.append("}")
    line.append(",")
    line.append("{")
    for i,R in enumerate(Rs):
        line.append("{")
        for j,row in enumerate(R.astype(np.int8)):
            s = str(row)
            s = s.strip("[]")                  # "  1  0 1"
            s = re.sub(r"\s+", ",", s)         # ",1,0,1"
            s = s.strip(",")                   # "1,0,1"
            s = "{" + s + "}"
            line.append(s)
            if j != len(R)-1:
                line.append(",")
        line.append("}")
        if i != len(Rs)-1:
            line.append(",")
    line += ["}","}",'"']
 
    with open(os.path.join(filepath), "w") as f:
        f.write("".join(line))
        f.close()

# Example Export from Mathematica: 
# Export["/home/pathto/SMw1.csv", {{{Ls, Rs}}}, "CSV"]


