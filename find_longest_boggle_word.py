def read_words(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file]


def is_valid_move(x, y, board, visited):
    return 0 <= x < len(board) and 0 <= y < len(board[0]) and not visited[x][y]


def search_word(board, word, index, x, y, visited):
    if index == len(word):
        return True

    if not is_valid_move(x, y, board, visited) or board[x][y] != word[index]:
        return False

    visited[x][y] = True

    # Explore all 8 possible directions
    for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
        if search_word(board, word, index + 1, x + dx, y + dy, visited):
            return True

    visited[x][y] = False
    return False


def can_form_word(board, word):
    visited = [[False] * len(board[0]) for _ in range(len(board))]
    for x in range(len(board)):
        for y in range(len(board[0])):
            if search_word(board, word, 0, x, y, visited):
                return True
    return False


def find_longest_word(board, words):
    longest_word = ''
    for word in words:
        if can_form_word(board, word):
            if len(word) > len(longest_word) or (len(word) == len(longest_word) and word < longest_word):
                longest_word = word
    return longest_word


# Boggle board
boggle_board = [
    ['A', 'B', 'R', 'L'],
    ['E', 'I', 'T', 'E'],
    ['I', 'O', 'N', 'S'],
    ['F', 'P', 'E', 'I']
]

# Read words from the dictionary
words = read_words('words_alpha.txt')

# Find the longest word
longest_word = find_longest_word(boggle_board, words)

longest_word