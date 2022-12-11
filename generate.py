import sys
import copy

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # Make a deepcopy to be able to loop through while
        # making changes to self.domains
        domain = copy.deepcopy(self.domains)

        # Node consistency is enforced when, for every variable
        # each value in its domain is consitent with its unary constraints
        for var in domain:
            for word in domain[var]:
                # Ensuring every value in a variables
                # domain has the same number of letters 
                # as the variables length
                if len(word) != var.length:
                    self.domains[var].remove(word)
        

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        # Make a deepcopy to be able to loop through while
        # making changes to self.domains
        domain = copy.deepcopy(self.domains)
        revised = False

        # Store the overlapping cells of the 
        # two variables
        x_overlap, y_overlap = self.crossword.overlaps[x, y]

        # If a cell of x does overlap with y, then revise
        if x_overlap:
            # Loop through the words in x's domain
            for x_word in domain[x]:
                # Keeps track of whether x_word has
                # matched with a word in y's domain
                matched = False
                for y_word in domain[y]:
                    if x_word[x_overlap] == y_word[y_overlap]:
                        matched = True
                        break
                # Remove any value from domain of x
                # that does not have a corresponding
                # value in the domain of y 
                if matched:
                    continue
                else:
                    self.domains[x].remove(x_word)
                    revised = True
                
        
        return revised
        

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # If arcs is None, we add all arcs in the csp
        if arcs is None:
            queue = []
            for var_1 in self.domains:
                for var_2 in self.crossword.neighbors(var_1):
                    if self.crossword.overlaps[var_1, var_2] is not None:
                        queue.append((var_1, var_2))
        
        # While queue is not empty
        while len(queue) != 0:
            # Dequeue (x,y) from queue
            x, y = queue.pop()

            # Runs the revise algorithm to see
            # if this arc is consistent
            if self.revise(x,y):
                # If the resulting domain of x is empty
                # then the csp is unsolvable
                if len(self.domains[x]) == 0:
                    return False

                # If the csp is not deemed unsolvable
                # then we need to check if all the arcs
                # associated with x are still consistent
                for neighbor in self.crossword.neighbors(x):
                    if neighbor != y:
                        queue.append((neighbor, x))
         
        # Returns true if arc consistency is enforced
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for var in self.domains:
            if var not in assignment.keys():
                return False

        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # An assignment is consistent if
        # - all values are distinct
        # - every value is of the correct length
        # - there are no conflicts between neighboring values

        # First we check if all values are distinct
        # We convert and store assignment.values() as list
        vals = [*assignment.values()]
        for val in vals:
            # If vals contains any value more than once
            # return False
            if vals.count(val) > 1:
                return False

        # Next we check if every value is of the correct length
        for var in assignment:
            if var.length != len(assignment[var]):
                return False
                    
        # Finally we check if there are any conflicts
        # between neighboring values
        for var in assignment:
            for neighbor in self.crossword.neighbors(var):
                if neighbor in assignment:
                    x, y = self.crossword.overlaps[var, neighbor]
                    if assignment[var][x] != assignment[neighbor][y]:
                        return False

        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        ordered_values = dict()
        for word in self.domains[var]:
            # Keep count of values that each word eliminates
            count = 0
            for neighbor in self.crossword.neighbors(var):
                # Any variable present in assignment already has
                # a value, therefore shouldn't be counted
                if neighbor in assignment:
                    continue
                
                x, y = self.crossword.overlaps[var, neighbor]
                for neighbor_word in self.domains[neighbor]:
                    if word[x] != neighbor_word[y]:
                        count += 1
            
            ordered_values[word] = count

        ordered_values = sorted(ordered_values)        

        return [*ordered_values]

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        unassigned_variables = dict()

        for var in self.domains:
            if var not in assignment:
                unassigned_variables[var] = self.domains[var]
        
        sorted_list = []
        for key, value in sorted(unassigned_variables.items(), key=lambda item:len(item[1])):
            sorted_list.append(key)
        
        return sorted_list[0]

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # If assignment complete
        if len(assignment) == len(self.domains):
            return assignment
        
        var = self.select_unassigned_variable(assignment)
        
        for value in self.order_domain_values(var, assignment):
            # Add {var = value} to assignment
            assignment_copy = assignment.copy()
            assignment_copy[var] = value

            if self.consistent(assignment_copy):
                result = self.backtrack(assignment_copy)
                if result is not None:
                    return result
        
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
