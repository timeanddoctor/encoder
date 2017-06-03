import time
import RPi.GPIO as GPIO

position      = 0
step_velocity = 0

def deg(pos):
    f = abs(pos) * 3.33333    # 3.333, constant from gears
    a = int(f) / 3600         # it means every changes on intterupt
    b = f - a*3600            # sensors will 3.33 arcsec motion on telescope
    c = int(b) / 60
    d = b - c*60
    e = d / 60
    
    if pos>0:
        return str(a) , str (c) , str(e)
    else:
        return str(359-a) , str (59-c) , str(59-e)

        
class encoder(object):
    """

    Encoder class for controlling stepper motor.
    Circuit based on RPi3 with two intterupt sensors
    which is fixxed on encoder disk and that disk fixxed
    on step motor's shaft.

    Starting motor and reading changes on default parameters

    encoder().start_stepper()
    default parameters are Interrupt pins = 2, 3
                           Step pins      = 6,13,19,26
                           Direction      = 1 (Clock-wise)
                           Step Speed     = 0.015
                           # Step speed's mean in every
                             15 ms motor will step.

    example: encoder(step_speed=0.001,direction=-1).start_stepper()
    
             Here in every 1 ms motor will 1 step in counter clock-wise
             direction.

    Going to spesific position: encoder().go_to(x)

             x is changing on intterupt sensors, if x = 1000 so motor
             will stop after 1000 changes.
    
    """
    def __init__(self,step_pins=[6, 13, 19, 26],
                 inter_pins=[2,3],
                 direction=1,
                 step_speed=0.015,
                 position=position):

        
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        
        self.step_pins = step_pins
        self.inter_pins = inter_pins
        self.direction = direction
        self.step_speed = step_speed
        self.mask = 1
        self.start_time1 = time.time()
        self.c = 0
        
        if self.direction == 1:
          self.step_seq = [1, 2, 4, 8]
        
        else:
          self.step_seq = [8, 4, 2, 1]

        for pin in self.inter_pins:
            GPIO.setup(pin, GPIO.IN)   

        for pin in self.step_pins:
            GPIO.setup(pin,GPIO.OUT)
            GPIO.output(pin, False)
    
    def start_intterupt(self):

        def cws_func(channel): #cw
            global position
            position += 1.0
            

        def acws_func(channel): #acw
            global position
            position -= 1.0

        func_co = None

        if self.direction == 1:
            func_co = cws_func
        else:
            func_co = acws_func

        for i in self.inter_pins:
            GPIO.add_event_detect(i,GPIO.FALLING,
                                  callback=func_co,
                                  bouncetime=5)  

    def go_to(self,pos):
        self.start_intterupt()
        try:
            while position != pos:
                    
                for i in range(4):
                    GPIO.output(self.step_pins[i],
                                self.mask & self.step_seq[i])
                self.mask = (((self.mask & 1)<< 4) | self.mask)>> 1
                time.sleep(self.step_speed)
        finally:
            [GPIO.remove_event_detect(i) for i in self.inter_pins]
            GPIO.cleanup()
            print deg(position)
                
    def start_stepper(self):
        self.start_intterupt()
        try:
            while True:
                global position,step_velocity
                for i in range(4):
                    GPIO.output(self.step_pins[i],
                                self.mask & self.step_seq[i])
                        
                self.mask = (((self.mask & 1)<< 4) | self.mask)>> 1

                if int(time.time()-self.start_time1)>4+self.c \
                   and int(time.time()-self.start_time1)<6+self.c:
                    print step_velocity
                    step_velocity = position / (5+self.c)
                    self.c       += 5

                time.sleep(self.step_speed)

        except KeyboardInterrupt:
            [GPIO.remove_event_detect(i) for i in self.inter_pins]
            GPIO.cleanup()
            print deg(position)


#encoder().start_stepper()

