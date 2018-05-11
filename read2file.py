import os

if os.path.exists("some.txt"): 
	my_file = open("some.txt")
	my_string = my_file.read()
	print("Было прочитано:")
	print(my_string)
	my_file.close()