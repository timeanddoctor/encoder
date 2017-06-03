import RPi.GPIO as GPIO, time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
reading=0

def RCtime(pin):
    global reading
    reading=0
    GPIO.setup(pin,GPIO.OUT)
    GPIO.output(pin,GPIO.LOW)
    time.sleep(0.0001)

    GPIO.setup(pin,GPIO.IN)
    while GPIO.input(pin) == GPIO.LOW:
        reading+=1

    return reading

t=int(time.time())
c=0
while 1:
    if int(time.time())-t==1+c:
        c=c+1
        print RCtime(21),c
