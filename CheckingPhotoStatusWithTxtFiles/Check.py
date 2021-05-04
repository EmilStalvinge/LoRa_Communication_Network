lastTaken=["1.jpg","2.jpg"]
lastSent=["1.jpg"]

SendPicture=True

while SendPicture:
#here camera capture, assume the new picture is "3.jpg"
	capture="3.jpg"
	lastTaken.append(capture)
	print(lastTaken)
	for picture in lastTaken:
		if picture not in lastSent:
			lastSent.append(picture)
			#send(picture)
			#print("sent")
			print(lastSent)
		else:  		
			print("Already Sent!")
			SendPicture=False
			break




