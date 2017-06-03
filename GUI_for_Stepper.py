import RPi.GPIO as GPIO
import sys, time
from PySide.QtGui import *
from PySide.QtCore import *

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

step_speed     = 0.5
step_pins      = [6, 13, 19, 26]
inter_pins     = [2,18]
direction      = 1
gear_constant  = 3.3333

go_to_position = 0
position       = 0
step_count     = 0
direction      = 1
lazer_pin      = 21
room_light     = 300
"""
step_seq = [[1, 0, 0, 1],
            [1, 0, 0, 0],
            [1, 1, 0, 0],
            [0, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 1],
            [0, 0, 0, 1]]
"""
step_seq = [[1, 1, 0, 1],
            [1, 0, 0, 0],
            [1, 0, 0, 1],
            [0, 0, 0, 1],
            [0, 0, 1, 1],
            [0, 0, 1, 0],
            [0, 1, 1, 0],
            [0, 1, 0, 0]]
            
def set_pins():
        GPIO.setup(step_pins,GPIO.OUT)
        GPIO.output(step_pins, False)
        
def setup_laz():
        GPIO.setup(lazer_pin,GPIO.OUT)
        GPIO.output(lazer_pin, False)
        time.sleep(0.0001)
        GPIO.setup(lazer_pin,GPIO.IN)
        
def clean_up():
        GPIO.cleanup(step_pins)
        GPIO.cleanup(lazer_pin)

def start_intterupt():
        global inter_pins
        
        GPIO.setup(inter_pins, GPIO.IN)
        
        def func_co(channel): 
                global position,direction
                if position == 360.0: 
                        position = 0
                if position == -1.0:
                        position = 359
                        
                if direction == 1:
                        position += 1.0
                        
                else:
                        position -= 1.0

        for i in inter_pins:
                GPIO.add_event_detect(i,GPIO.FALLING,
                                  callback=func_co,
                                  bouncetime=5)  

start_intterupt()
"""
def func_go(pos):
            p = [x.strip() for x in pos.split(',')]
            return int(p[0])*3600+int(p[1])*60+int(p[2])
"""
def deg(pos):
        f = abs(pos) * gear_constant
        a = f / 3600.0
        b = f - int(a)*3600.0
        c = b / 60.0
        d = b - int(c)*60
        a,c,d=int(a),int(c),int(d)
        if pos>0:
                return str(a) , str (c) , str(d)
        else:
                return str(359-a) , str (59-c) , str(59-d)

def step_func():
        global step_pins,step_seq,step_count
        pin_count = 0
        set_pins()
        for pin in step_pins:
                if step_seq[step_count][pin_count] == 1:
                        GPIO.output(pin,True)
                else:
                        GPIO.output(pin,False)
                        
                pin_count  += 1
                step_count += direction
                if step_count == 8 or step_count == -9:
                        step_count = 0


        
def laz_func(pin):
        lig=0
        setup_laz()
        while GPIO.input(pin) == GPIO.LOW:
                lig+=1
        return lig


class sig(QObject):
        sig = Signal(str)

class Go_To(QThread):
        def __init__(self, parent = None):
                QThread.__init__(self, parent)
                self.exiting = False
                self.signal = sig()
                

        def run(self):
                global position,go_to_position,step_pins,direction
                set_pins()
                
                if go_to_position == 360:
                        go_to_position = 0
                        
                if abs(position) - abs(int(go_to_position))<0:
                    direction = direction*-1

                    
                
                if go_to_position != '':
                        while self.exiting==False:
                                
                                step_func()

                                if int(go_to_position) == int(position):
                                    self.exiting=True
                                    direction = direction*-1
                                time.sleep(step_speed)

                       
                self.signal.sig.emit(str(go_to_position))
                
                
class StartStepper(QThread):
        def __init__(self, parent = None):
                
                QThread.__init__(self, parent)
                self.exiting   = False
                

        def run(self):
                while self.exiting==False:
                        step_func()                                
                        time.sleep(step_speed)


        
class home_pos_class(QThread):
        def __init__(self, parent = None):

                QThread.__init__(self, parent)
                self.exiting = False
                
        def run(self):
                global room_light,lazer_pin
                while self.exiting == False:
                        step_func()
                        if laz_func(lazer_pin)<room_light and laz_func(lazer_pin)!=0:

                                break
                        time.sleep(step_speed)


class StepMotorMotion(QMainWindow):
        def __init__(self, parent=None):
            
                QMainWindow.__init__(self,parent)
                self.centralwidget = QWidget(self)
                self.centralwidget.setWindowTitle('Control Step Motor')
                
                self.startstepbutton = QPushButton('Start Step Motor',self)
                
                self.homeposition = QPushButton('Home Position',self)
                self.gobutton = QPushButton('Go To',self)
                self.directioncheck = QCheckBox('Change direction', self)
                self.label1 = QLabel('Standing by')
                self.labelposition = QLabel('Position...')
                self.labelgo = QLabel('Go To:')
                self.sld = QDial(self)
                self.lcd = QLCDNumber(self)
                
                self.go_to_line = QLineEdit()
                self.vbox = QVBoxLayout()
                
                self.vbox.addWidget(self.startstepbutton)
                self.vbox.addWidget(self.directioncheck)
                self.vbox.addWidget(self.gobutton)
                self.vbox.addWidget(self.go_to_line)
                self.vbox.addWidget(self.labelgo)
                self.vbox.addWidget(self.label1)
                self.vbox.addWidget(self.homeposition)
                self.vbox.addWidget(self.labelposition)
                self.vbox.addWidget(self.lcd)
                self.vbox.addWidget(self.sld)
                self.setCentralWidget(self.centralwidget)
                self.centralwidget.setLayout(self.vbox)
                self.thread = StartStepper()
                self.go_to_thread = Go_To()
                self.home_pos_thread = home_pos_class()
                self.startstepbutton.clicked.connect(self.handletoggle)
                self.gobutton.clicked.connect(self.gooperation)
                self.thread.started.connect(self.started)
                self.thread.finished.connect(self.finished)
                self.thread.terminated.connect(self.terminated)
                self.go_to_thread.signal.sig.connect(self.gooperationcomplete)
                self.directioncheck.stateChanged.connect(self.changedirection)
                self.homeposition.clicked.connect(self.homepos)
                self.sld.sliderMoved.connect(self.display_speed)
        def started(self):
                global position
                self.label1.setText('Step Motor started')

        def finished(self):
                global position
                self.label1.setText('Step Motor stopped')

        def terminated(self):
                self.label1.setText('Step Motor terminated')

        def handletoggle(self):

                if self.thread.isRunning():
                        self.thread.exiting=True
                        self.startstepbutton.setEnabled(False)
                        
                        while self.thread.isRunning():
                                time.sleep(0.001)
                                continue
                        self.startstepbutton.setText('Start Step Motor')
                        self.startstepbutton.setEnabled(True)
                else:
                        
                        self.thread.exiting=False
                        self.thread.start()
                        self.startstepbutton.setEnabled(False)
                        while not self.thread.isRunning():
                                time.sleep(0.001)
                                clean_up() 
                                continue
                        self.startstepbutton.setText('Stop Step Motor')
                        self.startstepbutton.setEnabled(True)

        def gooperation(self):
                global go_to_position
                go_to_position = self.go_to_line.text()
                
                if not self.go_to_thread.isRunning():
                        self.go_to_thread.exiting=False
                        self.go_to_thread.start()
                        go_to_position = self.go_to_line.text()
                        self.labelgo.setText('Going to '+go_to_position)
                        self.gobutton.setEnabled(False)

        def gooperationcomplete(self,data):
                self.labelgo.setText('Last operation was '+data)
                self.gobutton.setEnabled(True)
                
        def changedirection(self,state):
                global direction,inter_pins
                if state == Qt.Checked:
                        direction = -1
                else:
                        direction = 1
                
                        
        def updateposition(self):
                global position,direction
                if direction == 1:
                        a='Clockwise'
                else:
                        a='Anti-Clockwise'
                self.labelposition.setText(str(position)+' '+a)

        def homepos(self):

                if self.home_pos_thread.isRunning():
                        self.home_pos_thread.exiting=True
                        self.homeposition.setEnabled(False)
                        
                        while self.home_pos_thread.isRunning():
                                time.sleep(0.001)
                                continue
                        self.homeposition.setText('Home position')
                        self.homeposition.setEnabled(True)
                else:
                        
                        self.home_pos_thread.exiting=False
                        self.home_pos_thread.start()
                        self.homeposition.setEnabled(False)
                        while not self.home_pos_thread.isRunning():
                                time.sleep(0.001)
                                clean_up() 
                                continue
                        self.homeposition.setText('Going to home')
                        self.homeposition.setEnabled(True)
                        
        def display_speed(self,data):
                global step_speed
                self.lcd.display(data)
                step_speed = 0.2*(201.0-float(data*2))/200.0+0.003



if __name__=='__main__':
        app = QApplication(sys.argv)
        window = StepMotorMotion()
        window.show()

        
        timer=QTimer()
        timer.timeout.connect(window.updateposition)
        timer.start(1)
        sys.exit(app.exec_())
