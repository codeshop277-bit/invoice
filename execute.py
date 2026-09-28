from pypdf import PdfReader
import pandas as pd
# Reverse a list using slicing and a for loop

def reverse_list(input_list):
    reversed_list = []
    for item in input_list[::-1]:
        reversed_list.append(item)
    return reversed_list
# print(reverse_list([1, 2, 3, 4, 5]))  # Output: [5, 4, 3, 2, 1]


# Find largest and smallest elements in a list
def find_largest_and_smallest(numbers):
    largest = float('-inf')
    smallest = float('inf')

    for number in numbers:
        if number < smallest:
            smallest = number
        if number > largest:
            largest = number

    return largest, smallest
# print(find_largest_and_smallest([3, 1, 4, 15, 9, 2, 6, -5, 3, 5]))  # Output: (9, 1)

def character_count(words):
    count = {}
    words = words.replace(" ", "")  # Remove leading and trailing whitespace
    for char in words.strip():
        if char in count:
            count[char] += 1
        else:
            count[char] = 1
    return count
# print(character_count("hello world"))  # Output: {'h': 1, 'e': 1, 'l': 3, 'o': 2, ' ': 1, 'w': 1, 'r': 1, 'd': 1}

def read_a_file(file_path):
    content = ""
    # with - purpose: to ensure that the file is properly closed after its suite finishes, even if an exception is raised at some point.
    with open(file_path, 'r') as file: #"r" - read mode, "w" - write mode, "a" - append mode, "r+" - read and write mode
        #  for line in file: # iterate over each line in the file
        # file.readlines()  # read all lines in the file and return a list of lines
         content = file.read()
    return content    

print(read_a_file("data.txt"))  # Output: Content of the file

def read_pdf(file_path):
    reader = PdfReader(file_path)
    pages =[]
    for page in reader.pages:
        text = page.extract_text()
        print(text)
    for page_number, page in enumerate(reader.pages):
        text = page.extracte_text()
        pages.append({"page_number": page_number + 1, "text": text})


def read_csv(file_path):
    df = pd.read_csv(file_path)
    records = df.to_dict(orient="records") #Converts to python dict
    rows, columns = df.shape
    print(len(df))
    print(len(df.columns))
    for index, rows in df.iterrows():
        print(rows)
    return df   
