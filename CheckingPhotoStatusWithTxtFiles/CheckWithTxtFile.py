#here camera capture, assume the new picture is "3.jpg"
TakenFile=open(r"lastTaken.txt","a+")
seekLine=0
capture="1.jpg"
copy=False
print(capture,file=TakenFile)
TakenFile.close()
with open(r"lastTaken.txt","r+") as Taken:
	with open("lastSent.txt","w+") as Sent:

		for line in Taken:
			
			if line not in Sent:
				Sent.write(line)
				
				
		


