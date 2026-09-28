# Pythin data structure

# Mutable means that the data structure can be changed after it is created.  Chnaged or edited or modified.
# Immutable means that the data structure cannot be changed after it is created.

a=[1, 2, 3, 4, 5]  # List
# Generic opeartions
a.pop()  # Removes and returns the last item from the data structure
a.clear()  # Removes all items from the data structure
a.copy()  # Returns a shallow copy of the data structure
a.count(1)  # Returns the number of occurrences of an item in the data structure
a.index(1)  # Returns the index of the first occurrence of an item in the data structure
a.reverse()  # Reverses the order of items in the data structure
a.sort()  # Sorts the items in the data structure in ascending order
a.sorted()  # Returns a new sorted list from the items in the data structure
a.insert(0, 10)  # Inserts an item at a specified index in the data structure
a.append(6)  # Adds an item to the end of the data structure

# List
a = [1,2,3,4,5 ]
# Lists are mutable, ordered collections of items. And Allows duplicate elements.
# They can contain elements of different data types, including other lists.

print(a)  # Output: [1, 2, 3, 4, 5]
print(a[0])  # Output: 1
a[1] = 20  # Modifying the second element
print(a)  # Output: [1, 20, 3, 4, 5]

a.append(6)  # Adding an element to the end of the list
a.remove(3)  # Removing an element from the list
a.insert(2, 15)  # Inserting an element at index 2

for item in a:  # Iterating over the list
    print(item)



#Tuple
a = (1, 2, 3, 4, 5)
# Tuples are immutable, ordered collections of items. They allow duplicate elements.
# They can contain elements of different data types, including other tuples.

print(a)  # Output: (1, 2, 3, 4, 5)
print(a[0])  # Output: 1
a[1] = 20  # This will raise an error because tuples are immutable
a.append(6)  # This will also raise an error because tuples are immutable
for item in a:  # Iterating over the tuple
    print(item)

# Set
a = {1, 2, 3, 4, 5}
# Sets are mutable, unordered collections of unique items. They do not allow duplicate elements.
# They can contain elements of different data types, but not other sets.

print(a)  # Output: {1, 2, 3, 4, 5}
print(1 in a)  # Output: True
print(6 in a)  # Output: False
a.add(6)  # Adding an element to the set
a.remove(3)  # Removing an element from the set
print(a)  # Output: {1, 2, 4, 5, 6}
a.add(2)  # This will not add a duplicate element to the set
a.remove(10)  # This will raise a KeyError because 10 is not in the set
a.remove(1) # This will remove the element 1 from the set

b = {4, 5, 6, 7, 8}
print(a.union(b))  # Output: {1, 2, 4, 5, 6, 7, 8}
print(a.intersection(b))  # Output: {4, 5, 6}
print(a.difference(b))  # Output: {1, 2}

for item in a:  # Iterating over the set
    print(item)


# Dictionary
a = {"one": 1, "two": 2, "three": 3}
# Dictionaries are mutable, unordered collections of key-value pairs. They do not allow duplicate keys.
# They can contain elements of different data types, including other dictionaries.

print(a)  # Output: {'one': 1, 'two': 2, 'three': 3}
print(a["one"])  # Output: 1

a["one"] = 10  # Modifying the value associated with the key "one"
a["four"] = 4  # Adding a new key-value pair to the dictionary

del a["two"]  # Removing the key-value pair with the key "two"

for key, value in a.items():  # Iterating over the key-value pairs in the dictionary
    print(f"{key}: {value}")

# String
a = "Hello, World!"
# Strings are immutable, ordered collections of characters. They allow duplicate characters.
print(a)  # Output: Hello, World!
print(a[0])  # Output: H

a = a.replace("World", "Python")  # This will create a new string with the replacement
print(a)  # Output: Hello, Python!

a = a.upper()  # This will create a new string with all uppercase characters
a = a.lower()  # This will create a new string with all lowercase characters
a = a.strip()  # This will create a new string with leading and trailing whitespace removed
a = a.split(",")  # This will create a list of substrings by splitting the string at the comma

for char in a:  # Iterating over the characters in the string
    print(char)

# Range
#It is an immutable sequence of numbers that is commonly used for looping a specific number of times in for loops.
a = range(5)  # Creates a range object representing the numbers 0 to
print(a)  # Output: range(0, 5)
for num in a:  # Iterating over the numbers in the range
    print(num)  # Output: 0, 1, 2, 3, 4

# float
# Floats are immutable, ordered collections of numbers with decimal points. They allow duplicate values.
a = 3.14
a = a + 1.0  # This will create a new float with the addition

a= 2.71 # This will create a new float with the addition



# Code execution
a = [1, 2, 3, 4, 5]
b = a
# Modifying the original list, because b is a reference to the same list object as a
# to avoid this we can use copy() method to create a shallow copy of the list
b = a.copy()  # Creates a shallow copy of the list  
# TO create a deep copy of the list, we can use the deepcopy() method from the copy module
b = copy.deepcopy(a)  # Creates a deep copy of the list

# Coding questions
Input:  "hello"
Output: "olleh"