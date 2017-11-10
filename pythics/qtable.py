# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2017 Anton Velo <avelo@iim.csic.es>
#
#
from PyQt5 import QtCore, QtGui, QtWidgets


import pythics.lib
import pythics.libcontrol

import multiprocessing
import re
import pandas as pd

#
#
#
class QTableModel(QtCore.QAbstractTableModel):
    def __init__(self, datain=[[]], parent=None, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.arraydata=datain

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.arraydata)
    def columnCount(self, parent=QtCore.QModelIndex()):
        if len(self.arraydata) > 0:
            return len(self.arraydata[0])
        return 0
    def data(self, index, role):
        if not index.isValid():
            return '' #QtCore.QVariant()
        #elif role != QtCore.Qt.DisplayRole:
        #    return '' #QtCore.QVariant()
        row=index.row()
        column=index.column()
        if(row<self.rowCount() & column<self.columnCount()):
            return self.arraydata[row][column]
        else:
            return ''
    def topLeft(self):
        return self.index(0,0)
    def bottomRight(self):
        return self.index(self.rowCount()-1,self.columnCount()-1)
    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if index.isValid():
            if role == QtCore.Qt.EditRole:
                row = index.row()
                column = index.column()
                self.arraydata[row][column] = value
                #setattr(self.arraydata[index.row()], self.columns[index.column()], value)
                #self.dataChanged.emit(index, index, [QtCore.Qt.EditRole])
                #self.dataChanged(self.topLeft(),self.bottomRight())
                self.emit(QtCore.SIGNAL("layoutChanged()"))
                return True
        return False
    def flags(self, index):
        #return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
        return QtCore.Qt.ItemIsEnabled |  QtCore.Qt.ItemIsEditable


#
# Custom QTableWidget:
#
class QTW(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        QtWidgets.QTableWidget.__init__(self)
        self.pddf=pd.DataFrame()
        self.clipboard = QtWidgets.QApplication.clipboard()

    def extract_data(self):
        #logger=multiprocessing.get_logger()
        #logger.debug('Extracting data')
        colCount=self.columnCount()
        rowCount=self.rowCount()
        self.pddf=pd.DataFrame()
        for c in range(0,colCount):
            try:
                h=self.horizontalHeaderItem(c).text()
            except:
                h=str(c+1)
            for r in range(0,rowCount):
                try:
                    try:
                        t=float(self.item(r,c).text())
                    except:
                        t=str(self.item(r,c).text())
                except:
                    t=''
                try:
                    self.pddf.set_value(r,h,t)
                except:
                    self.pddf=self.pddf.fillna('')
                    self.pddf.set_value(r,h,t)

        return self.pddf

    def copy(self):
        logger=multiprocessing.get_logger()
        logger.debug('Copying from table:')
        selected = self.selectedRanges()
        #logger.debug('%d %d\n%d %d'%(selected[0].topRow(),selected[0].leftColumn(),selected[0].bottomRow(),selected[0].rightColumn()))
        s=''
        #s = '\t'+"\t".join([str(self.horizontalHeaderItem(i).text()) for i in xrange(selected[0].leftColumn(), selected[0].rightColumn()+1)])
        #s = s + '\n'
        for r in range(selected[0].topRow(), selected[0].bottomRow()+1):
            #s += self.verticalHeaderItem(r).text() + '\t'
            for c in range(selected[0].leftColumn(), selected[0].rightColumn()+1):
                try:
                    s += str(self.item(r,c).text()) + "\t"
                except AttributeError:
                    s += "\t"
            s = s[:-1] + "\n" #eliminate last '\t'
        logger.debug('\n%s'%(s))
        self.clipboard.setText(s)

    def paste(self):
        logger=multiprocessing.get_logger()
        logger.debug('Pasting to table:')
        pt=self.clipboard.text()
        #logger.debug('%s'%(pt))
        try:
            rows=re.split(r"[\r|\n|(\r\n)]+",pt)
            numRows=len(rows)
            numCols=rows[0].count('\t')+1
            logger.debug('%d rows, %d cols'%(numRows,numCols))
            selectionRanges=self.selectionModel().selection()
            if len(selectionRanges)==1:
                topLeftIndex=selectionRanges[0].topLeft()
                selColumn=topLeftIndex.column()
                selRow=topLeftIndex.row()
                # if selColumn+numCols>model.columnCount():
                #     #the number of columns we have to paste, starting at the selected cell, go beyond how many columns exist.
                #     #insert the amount of columns we need to accomodate the paste
                #     model.insertColumns(model.columnCount(), numCols-(model.columnCount()-selColumn))
                #
                # if selRow+numRows>model.rowCount():
                #     #the number of rows we have to paste, starting at the selected cell, go beyond how many rows exist.
                #     #insert the amount of rows we need to accomodate the paste
                #     model.insertRows(model.rowCount(), numRows-(model.rowCount()-selRow))

                for r in range(numRows):
                    cols=rows[r].split('\t')
                    for c in range(numCols):
                        #[model.setData(model.createIndex(selRow+row, selColumn+col), QVariant(columns[col])) for col in xrange(len(columns))]
                        self.setItem(selRow+r, selColumn+c, QtWidgets.QTableWidgetItem(cols[c]))
        except:
            logger.debug('Error trying to paste: %s',pt)
            pass

#
# Custom Table control:
#
class QTableW(pythics.libcontrol.Control):
    """
    """
    def __init__(self, parent, **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = QTW()
        self.clipboard = QtWidgets.QApplication.clipboard()
        #self._widget.horizontalHeader().setHighlightSections(False)
        self.hh=self._widget.horizontalHeader()
        self.headers=[]

    def setItem(self,row,column,value):
        item=QtWidgets.QTableWidgetItem(value)
        self._widget.setItem(row,column,item)
        self.resizeColumnToContents(column)

    def item(self,row,column):
        return self._widget.item(row,column)

    def setRowCount(self,rows):
        self._widget.setRowCount(rows)

    def setColumnCount(self,columns):
        self._widget.setColumnCount(columns)

    def setHorizontalHeaderLabels(self,qsl):
        self._widget.setHorizontalHeaderLabels(qsl)
        self.headers=qsl
    def resizeColumnsToContents(self):
        self._widget.resizeColumnsToContents()

    def resizeColumnToContents(self, col):
        self._widget.resizeColumnToContents(col)

    def extract_data(self):
        return self._widget.extract_data()

    def getWidget(self):
        return self._widget
