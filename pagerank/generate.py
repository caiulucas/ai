import copy
import itertools
import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Inicializa um novo gerador de palavras cruzadas.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Retorna uma matriz 2D representando uma atribuição de palavras ao tabuleiro.
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
        Imprime a solução do jogo no terminal.
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
        Salva a solução do jogo em um arquivo de imagem.
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
        Aplica a consistência de nós e arcos e depois resolve o CSP (Problema de Satisfação de Restrições).
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Garante que cada variável seja consistente em relação a si mesma, ou seja,
        remove palavras cujo comprimento não corresponde ao esperado.
        """
        for variable in self.domains:
            remove_word = set()
            for word in self.domains[variable]:
                if len(word) != variable.length:
                    remove_word.add(word)
            for word in remove_word:
                self.domains[variable].remove(word)

    def revise(self, x, y):
        """
        Torna `x` arc-consistente com `y` removendo valores de `x`
        que não possuem correspondência em `y`.
        Retorna True se alguma alteração for feita, senão False.
        """
        revised = False
        overlap = self.crossword.overlaps[x, y]
        if overlap is not None:
            remove_word = set()
            for x_word in self.domains[x]:
                overlap_char = x_word[overlap[0]]
                corresponding_y_chars = {w[overlap[1]] for w in self.domains[y]}

                if overlap_char not in corresponding_y_chars:
                    remove_word.add(x_word)
                    revised = True
            for word in remove_word:
                self.domains[x].remove(word)

        return revised

    def ac3(self, arcs=None):
        """
        Aplica o algoritmo AC-3 para garantir a consistência de arco.
        """
        if arcs is None:
            queue = list(itertools.product(self.crossword.variables, self.crossword.variables))
            queue = [arc for arc in queue if arc[0] != arc[1] and self.crossword.overlaps[arc[0], arc[1]] is not None]
        else:
            queue = arcs
        while queue:
            arc = queue.pop(0)
            x, y = arc[0], arc[1]
            if self.revise(x, y):
                if not self.domains[x]:
                    print("ending ac3")
                    return False
                for z in (self.crossword.neighbors(x) - {y}):
                    queue.append(((z, x)))
        return True

    def assignment_complete(self, assignment):
        """
        Verifica se todas as variáveis foram atribuídas.
        """
        if set(assignment.keys()) == self.crossword.variables and all(assignment.values()):
            return True
        else:
            return False

    def consistent(self, assignment):
        """
        Verifica se a atribuição de palavras é válida.
        """
        if len(set(assignment.values())) != len(set(assignment.keys())):
            return False
        if any(variable.length != len(word) for variable, word in assignment.items()):
            return False

        for variable, word in assignment.items():
            for neighbor in self.crossword.neighbors(variable).intersection(assignment.keys()):
                overlap = self.crossword.overlaps[variable, neighbor]
                if word[overlap[0]] != assignment[neighbor][overlap[1]]:
                    return False

        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        num_choices_eliminated = {word: 0 for word in self.domains[var]}
        neighbors = self.crossword.neighbors(var)
        for word_var in self.domains[var]:
            for neighbor in (neighbors - assignment.keys()):
                overlap = self.crossword.overlaps[var, neighbor]
                for word_n in self.domains[neighbor]:
                    if word_var[overlap[0]] != word_n[overlap[1]]:
                        num_choices_eliminated[word_var] += 1
        sorted_list = sorted(num_choices_eliminated.items(), key=lambda x: x[1])
        return [x[0] for x in sorted_list]

    def select_unassigned_variable(self, assignment):
        """
    Retorna uma variável não atribuída que ainda não faz parte de `assignment`.
    Escolhe a variável com o menor número de valores restantes no seu domínio.
    Se houver empate, escolhe a variável com o maior grau (número de vizinhos).
    Se ainda houver empate, qualquer uma das variáveis empatadas pode ser retornada.
    """
        unassigned_variables = self.crossword.variables - assignment.keys()

        # Número de valores restantes no domínio de cada variável
        num_remaining_values = {variable: len(self.domains[variable]) for variable in unassigned_variables}
        sorted_num_remaining_values = sorted(num_remaining_values.items(), key=lambda x: x[1])

        # Se não houver empate, retorna a variável com o menor número de valores restantes no domínio
        if len(sorted_num_remaining_values) == 1 or sorted_num_remaining_values[0][1] != sorted_num_remaining_values[1][
            1]:
            return sorted_num_remaining_values[0][0]

        # Se houver empate, retorna a variável com o maior número de vizinhos (grau)
        else:
            num_degrees = {variable: len(self.crossword.neighbors(variable)) for variable in unassigned_variables}
            sorted_num_degrees = sorted(num_degrees.items(), key=lambda x: x[1], reverse=True)
            return sorted_num_degrees[0][0]



    def backtrack(self, assignment):
            """
            Usa busca por retrocesso (Backtracking Search) para encontrar uma atribuição
            completa do problema do caça-palavras.

            `assignment` é um dicionário que mapeia variáveis (chaves) para palavras (valores).

            Se nenhuma atribuição for possível, retorna None.
            """
            if self.assignment_complete(assignment):
                return assignment

            var = self.select_unassigned_variable(assignment)
            for value in self.order_domain_values(var, assignment):
                test_assignment = copy.deepcopy(assignment)
                test_assignment[var] = value
                if self.consistent(test_assignment):
                    assignment[var] = value
                    result = self.backtrack(assignment)
                    if result is not None:
                        return result
                assignment.pop(var, None)
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