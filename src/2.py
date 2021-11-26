#!python

from PyQt5 import QtSql
from PyQt5 import QtCore
import time
from PyQt5 import QtWidgets , QtGui, uic
from PyQt5.QtWidgets import QHeaderView, QMessageBox, QTableView
import sys
from PyQt5.QtCore import QDateTime, QElapsedTimer, QItemSelectionModel, QSize, QTime,QTimer, Qt, QVariant, QThread, pyqtSignal
import pandas as pd 
from PyQt5.QtSql import QSqlQuery, QSqlTableModel

## ==> GLOBALS 
counter  = 0
headers =  ["Book", "Author", "Reading Time", "Started", "Finished", "Status", "Select"]
### TABLE MODEL 

class TableModel(QtCore.QAbstractTableModel):
    
    def __init__( self, data ):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
    
    def rowCount(self, index) -> int:
        return len(self._data)


    def columnCount(self, index) -> int:
        return len(self._data[0])

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole :

            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section])


class AddBook(QtWidgets.QMainWindow):

    def __init__(self) -> None:
        super(AddBook,self).__init__()
        
        self.book = uic.loadUi( "bookAdd.ui", self )
        self.book.addBook.clicked.connect( self.addButton )

    def addButton( self ):
        
        bookName = self.book.bookName.text()
        authorName = self.book.authorName.text()
        startDate = "-".join(map(str,[ self.book.startDate.date().year() , self.book.startDate.date().month() , self.book.startDate.date().day() ]))
        
        endDate = "-".join(map(str,[ self.book.endDate.date().year() , self.book.endDate.date().month() , self.book.endDate.date().day() ]))
        
        timeEdit = [ self.book.timeEdit.time().hour() ,  self.book.timeEdit.time().minute() ]
        
        time = (timeEdit[0] * 60 + timeEdit[1]) * 60 
        
        status = 1 if self.book.currentlyReading.isChecked() else 0
        
        # currentlyReading = self.book.currentlyReading.isChecked()
        # stats = [ bookName, authorName, startDate, endDate, timeEdit, currentlyReading ]

        db = BookTrackerApp.dbConnection()
        query = QSqlQuery()
        query.exec_(f"INSERT INTO books (book_name,author_name,read_time,started_date,finished_date,status) VALUES ('{bookName}','{authorName}',{time},'{startDate}','{endDate}','{status}')")
        
        self.book.close()


## Custom timer trigger signal
class Example(QtCore.QObject):

    my_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()

    @QtCore.pyqtSlot()
    def run(self):
        while True:

            self.my_signal.emit()
            time.sleep(0.1)


class BookTrackerApp(QtWidgets.QMainWindow):

    def control(self):
        try:
            open("book.db")
        except:
            return "FileNotFoundError" 
        

    def __init__(self):
        super(BookTrackerApp, self).__init__()

        self.ui = uic.loadUi( "untitled.ui", self )

        QtCore.QTimer.singleShot( 0, lambda: self.ui.welcomeText.setStyleSheet( "background-color: #222; color: #FFF;" ))
        QtCore.QTimer.singleShot( 0, lambda: self.ui.welcomeText.setText( "<strong>WELCOME, </strong>HYP£RI0NNN" ))
        QtCore.QTimer.singleShot( 1500, lambda: self.ui.welcomeText.setText( "<strong>LET'S </strong>READ" ))

        self.check = self.control()
        # print("self.check --> " + str(self.check))
        # print(self.check)

        ### CHECK DB IS EXISTS
        if self.check == "FileNotFoundError":      
            # print("file not found and created.")
            self.firstUse()
        
        ### LOAD TABLE FROM DB
        self.refresh()


        ### Clock variables
        self.save = "00:00:00:00"
        self._play = False
        self._second = 0 
        self._minute = 0 
        self._hour = 0
        self._msec = 0

        # set timer items
        self.worker = Example()
        self.workerThread = QtCore.QThread()
        self.workerThread.started.connect(self.worker.run)
        self.worker.moveToThread(self.workerThread)
        self.worker.my_signal.connect(self.showStopwatch)

        self.load_save()
        self.set_save_to_variables()
        self.set_to_clock()

        # Icons
        start_icon = QtGui.QPixmap("icons/start.webp")       
        self.clockStart.setIcon(QtGui.QIcon(start_icon))
        self.clockStart.setIconSize(QSize(28, 28))
        pause_icon = QtGui.QPixmap("icons/p.webp")       
        self.clockPause.setIcon(QtGui.QIcon(pause_icon))
        self.clockPause.setIconSize(QSize(28, 28))
        reset_icon = QtGui.QPixmap("icons/res.webp")       
        self.clockReset.setIcon(QtGui.QIcon(reset_icon))
        self.clockReset.setIconSize(QSize(28, 28))
        # add_book_Icon = QtGui.QPixmap("icons/book.webp")       
        add_Icon = QtGui.QPixmap("icons/dd.webp")       
        # self.clockToBook.setIcon(QtGui.QIcon(add_book_Icon))
        self.clockToBook.setIcon(QtGui.QIcon(add_Icon))
        self.clockToBook.setIconSize(QSize(28, 28))
        self.setWindowIcon(QtGui.QIcon("book.webp"))

        ### => BUTTONS 
        self.refreshBooks.clicked.connect(self.refresh)
        self.addBooks.clicked.connect(self.addNewBook)
        self.deleteBooks.clicked.connect(self.delete_book)
        self.clockStart.clicked.connect(self.play)
        self.clockPause.clicked.connect(self.pause)
        self.clockReset.clicked.connect(self.reset)
        # add register time to book
        self.clockToBook.clicked.connect(self.add_time_to_book)
        self.get_currently_reading()
    

    def firstUse(self):

        db = self.dbConnection()
        
        query = QtSql.QSqlQuery("Create table books(id integer PRIMARY KEY AUTOINCREMENT, book_name text , author_name text,read_time integer,started_date text,finished_date text,status integer)")

        # insert_query = QtSql.QSqlQuery()
        query.exec_("INSERT INTO books (book_name,author_name,read_time,started_date,finished_date,status) VALUES ('example','author',400,'2010-10-10','2011-10-10','1')")
        
        db.close()
        # self.ui.newTable.hideColumn(0)
        # self.ui.newTable.hideColumn(1)


    @classmethod
    def dbConnection(self):
        db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        db.setDatabaseName("book.db")
        if db.open():
            print("Connection Established /// ")
            
        return db


    def refresh(self): 
        db = self.dbConnection()
        # print ( db.isOpen() )
        # query = QSqlQuery("Select * from books")
        model = QtSql.QSqlTableModel()
        model.setTable("books")
        model.select()
         
        self.ui.newTable.setModel(model)
        self.newTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.newTable.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.ui.newTable.hideColumn(0)  # hide id section
        self.get_currently_reading()
        db.close()
        # print (db.isOpen())


    def addNewBook(self):
        self.book = AddBook()
        self.book.show()


    def delete_book(self):

        db = self.dbConnection()
        # print("ready to delete")
        selections = self.newTable.selectionModel().selectedRows()
        for s in selections:
            row_index = s.row() 
            id = s.data()
            # print(row_index, id)
            # print(s.row())

            query = QSqlQuery(f"Select * from books where id={id}")
            index = query.record().indexOf('id')
            name = query.record().indexOf('book_name')
            author = query.record().indexOf('author_name')
            while query.next():
                n = query.value(name)
                a = query.value(author)
                # print(query.value(index))
                # print(n)
                # print(a)
            
                pop_up = QMessageBox()

                pop_up.setWindowTitle("Are you sure")
                pop_up.setText(f"You want to delete {n.title()}, {a.title()} ")
                pop_up.setIcon(QMessageBox.Question)
                pop_up.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
                return_value = pop_up.exec_()

                if return_value == QMessageBox.Yes:
                    
                    q = QSqlQuery(f"DELETE FROM books where id={id}")
                    q.exec_()
                    info_box = QMessageBox()
                    info_box.setText(f"{n} {a} deleted!")
                    info_box.exec_()
                    
        self.refresh()   
    
    def get_currently_reading(self):
        
        self.currentBook.clear()
        db = self.dbConnection()
        # print("getting currently readings...")
        items = []
        query = QSqlQuery("Select * from books where status=1")
        index = query.record().indexOf('id')
        name = query.record().indexOf('book_name')
        author = query.record().indexOf('author_name')
        while query.next():
            temp = []
            n = query.value(name)
            a = query.value(author)

            temp.append(n)
            temp.append(a)

            item = ", ".join(temp)
            # print(item)
            items.append(item)

        self.currentBook.addItems(items)


    # write to last session file
    def set_last_session(self):

        with open("last_save.dat","w") as last:
            last.write(self.save + "\n")


    # laod from last session file
    def load_save(self):

        try:
            open("last_save.dat","r")     
        except FileNotFoundError as e:
            print(e)
        else:
            with open("last_save.dat","r") as file:
                line = file.readline()                
            
            self.set_clock_to_save(line)
            self.ui.clockDisplay.setText(self.save)


    # set self.save to local clock variables
    def set_save_to_variables(self):

        time_stamps = self.save.strip().split(":")        
        self._hour = int(time_stamps[0])
        self._minute = int(time_stamps[1])
        self._second = int(time_stamps[2])
        self._msec = int(time_stamps[3])


    # set current clock to self.save session
    def set_clock_to_save(self,time):
        t = time.strip().split(":")
        # print(t)
        # _h = f"{self._hour:02}"
        # _m = f"{self._minute:02}"
        # _s = f"{self._second:02}"
        # _ms = f"{self._msec:02}"
        _h = f"{int(t[0]):02}"
        _m = f"{int(t[1]):02}"
        _s = f"{int(t[2]):02}"
        _ms = f"{int(t[3]):01}"

        clock = f"{_h}:{_m}:{_s}:{_ms}"
        self.save = clock


    # set self.save to display section
    def set_to_clock(self):
         self.ui.clockDisplay.setText('<h1>' + self.save + '</h1>')


    def play(self):
        
        ####  CUSTOM TIMER START        
        self._play = True
        self.workerThread.start()


    def pause(self):
        self._play = False
        save = f"{self._hour}:{self._minute}:{self._second}:{self._msec}"
        self.save = save
        self.set_last_session()


    def reset(self):
        self.save = "00:00:00:00"
        self.set_save_to_variables()
        self.set_clock_to_save(self.save)
        self.set_last_session()
        self.set_to_clock()

    
    def showStopwatch(self):
        
        if self._play:
            self._msec += 1

            if self._msec > 9:
                self._second += 1
                self._msec = 0

            # self._second += 1

            if self._second > 59:
                self._second = 0
                self._minute += 1
            
            if self._minute > 59:
                self._minute = 0
                self._hour += 1

        clock = f"{self._hour:02}:{self._minute:02}:{self._second:02}:{self._msec:01}"

        self.ui.clockDisplay.setText('<h1>' + clock + '</h1>')


    def add_time_to_book(self):

        current_book = self.currentBook.currentText()
        current_book_index = self.currentBook.currentIndex()
        current_book = current_book.split(",")
        book_name = current_book[0].strip()
        
        prepare_time = (self._hour * 60 * 60) + (self._minute * 60) + (self._second)
        db = self.dbConnection()                
        query = QSqlQuery(f"Select * from books where status=1")
        
        name = query.record().indexOf('book_name')
        time = query.record().indexOf("read_time")
        # print(time)
        while query.next():
            if query.value(name) == book_name:
                read_time = query.value(time)
                # print (str(read_time) + " current_read_time")
                read_time += prepare_time
                # print (str(read_time) + " updated_read_time")
                # data = [book_name, read_time]
                q = QSqlQuery()
                q.prepare("UPDATE books SET read_time = (?) WHERE book_name = (?)")
                q.addBindValue([read_time])
                q.addBindValue([book_name])
                if not q.execBatch():
                    print(q.lastError())

        self.currentBook.itemText(current_book_index)
  
##### DONT REMOVE 
# 
# SPLASH SCREEN     
class SplashScreen(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super(SplashScreen,self).__init__()

        ## ==> LOAD UI 
        self.ui = uic.loadUi( "splashScreen.ui", self )

        ## REMOVE TITLE BAR
        self.setWindowFlag( QtCore.Qt.FramelessWindowHint )
        self.setAttribute( QtCore.Qt.WA_TranslucentBackground )

        ## DROP SHADOW EFFECT
        self.shadow = QtWidgets.QGraphicsDropShadowEffect( self )
        self.shadow.setBlurRadius( 100 )
        self.shadow.setXOffset( 0 )
        self.shadow.setYOffset( 0 )
        self.shadow.setColor( QtGui.QColor( 0, 0, 0, 60 ) )

        ##  QTIMER 
        self.timer = QTimer()
        self.timer.timeout.connect( self.progress )
        # TIMER REFRESH RATE IN MS
        self.timer.start( 20 )

        ## CHANGE DESCRIPTION
        self.ui.label_description.setText( "<strong>WELCOME</strong>TO BOOK TRACKER" )
        QtCore.QTimer.singleShot( 800, lambda: self.ui.label_description.setText( "<strong>LOADING </strong>DATABASE" ))
        QtCore.QTimer.singleShot( 1400, lambda: self.ui.label_description.setText( "<strong>LOADING </strong>USER INTERFACE" ))
        QtCore.QTimer.singleShot( 2000, lambda: self.ui.label_description.setText( "<strong>COUNTING </strong>BOOKS" ))

        ## SHOW MAIN WINDOW
        self.show()
        
        ## ==> -- END -- ==> ## 


    ## ==> FUNCTIONS 

    def progress(self):

        global counter
        self.ui.progressBar.setValue( counter )

        if counter > 100:            
            ## TIMER STOP 
            self.timer.stop()

            ## SHOW MAIN WINDOW
            self.main = BookTrackerApp()
            self.main.show()

            ## CLOSE SPLASH SCREEN
            self.close()

        ## INCREASE COUNTER
        counter += 1



if __name__ == "__main__":
    
    app = QtWidgets.QApplication(sys.argv)
    win = SplashScreen()
    win.show()
    sys.exit(app.exec_())



