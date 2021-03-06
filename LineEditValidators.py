"""
 * Universal line edit validator. Used for various dialog boxes.
 *
 * Copyright (c) 2018 Michail Kurochkin
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 """

from PyQt5.QtGui import *
from ElectroEditor import *
from GraphicsItem import *


class DialogLineEditValidator(QValidator):
    invalidSymbols = "~!@#$%^&*()=+{}[]\/,"
    def __init__(self, editor, lineEdit=None):
        QValidator.__init__(self)
        if lineEdit:
            self.lineEdit = lineEdit
        self.editor = editor


    def setLineEdit(self, lineEdit):
        self.lineEdit = lineEdit


    def stringIsValid(self, string):
        for sym in string:
            if self.invalidSymbols.find(sym) >= 0:
                return False
        return True


    def sendOkMessage(self, message):
        self.lineEdit.setStyleSheet("color: green")
        self.editor.showStatusBarMessage(message)


    def sendError(self, message):
        self.lineEdit.setStyleSheet("color: red")
        self.editor.showStatusBarErrorMessage(message)


    def fixup(self, string):
        pass




class ComponentNameValidator(DialogLineEditValidator):
    def __init__(self, editor, lineEdit=None):
        DialogLineEditValidator.__init__(self, editor, lineEdit)


    def validate(self, string, pos):
        string = str(string)
        if not self.stringIsValid(string):
            return QValidator.Invalid, string, pos

        words = string.split()
        if len(words) != 2:
            self.sendError("Please enter component_name and component_prefix through a space")

        if len(words) > 1:
            prefix = words[1]
        else:
            prefix = ""
        if not len(words):
            return QValidator.Invalid, string, pos
        name = words[0]

        for component in self.editor.componentList:
            if component.name() == name:
                self.sendError("component with name '%s' already exists" % name)
                return QValidator.Intermediate, string, pos

        self.sendOkMessage("OK! Component name:'%s' and prefix:'%s'" %
                           (name, prefix))
        return QValidator.Acceptable, string, pos




class YesNoValidator(DialogLineEditValidator):
    def __init__(self, editor, lineEdit=None):
        DialogLineEditValidator.__init__(self, editor, lineEdit)


    def validate(self, string, pos):
        string = str(string).lower()
        if (string != 'yes' and string != 'y' and
            string != 'no' and string != 'n'):
            self.sendError("Enrer Yes or No")
            return QValidator.Intermediate, string, pos

        self.sendOkMessage("OK")
        return QValidator.Acceptable, string, pos




class EditGroupValidator(DialogLineEditValidator):
    def __init__(self, editor, group):
        DialogLineEditValidator.__init__(self, editor)
        self.group = group


    def validate(self, string, pos):
        string = str(string).upper()
        if not self.stringIsValid(string):
            return QValidator.Invalid, string, pos

        if not len(string):
            return QValidator.Acceptable, string, pos

        # string can not begin with digit
        if string.isdigit():
            return QValidator.Invalid, string, pos

        unpackedName = self.editor.unpackGroupIndexName(string)

        # space for after complete
        if string[-1] == ' ':
            if len(string) == 1:
                return QValidator.Invalid, string, pos

            if string[-2].isdigit():
                return QValidator.Invalid, string, pos

            if string[-2] == '.':
                indexName = self.editor.packGroupIndexName(unpackedName)
                parentGroup = self.editor.findGroupByIndexName(indexName, self.group)
                if not parentGroup:
                    self.sendError("parent component '%s' not exists" % indexName)
                    return QValidator.Invalid, pos
                prefix = "%s." % parentGroup.indexName()
                index = self.editor.findFreeSubComponentIndex(parentGroup)
            else:
                prefix = string[:-1]
                index = self.editor.findFreeComponentIndex(string[:-1])

            self.lineEdit.setText("%s%d" % (prefix, index))
            return QValidator.Invalid, string, pos

        # check for multiple name
        if string[-1].find('.') > 0:
            if not unpackedName[2]:
                self.sendError("Not complete")
                return QValidator.Intermediate, string, pos

            indexName = self.editor.packGroupIndexName(unpackedName[:-1])
            group = self.editor.findGroupByIndexName(indexName, self.group)
            if not group:
                self.sendError("Parent component '%s' not exists" % indexName)
                return QValidator.Intermediate, string, pos
            self.sendOkMessage("OK")
            return QValidator.Acceptable, string, pos

        # check for name's busyness
        group = self.editor.findGroupByIndexName(string, self.group)
        if group:
            self.sendOkMessage("component '%s' already exists! Compnent will be overwritten!" % string)
            return QValidator.Acceptable, string, pos

        self.sendOkMessage("OK")
        return QValidator.Acceptable, string, pos




class ConnectinValidator(DialogLineEditValidator):
    def __init__(self, editor):
        DialogLineEditValidator.__init__(self, editor)


    def validate(self, string, pos):
        validsymbols = "0123456789 "
        string = str(string)
        if not self.stringIsValid(string):
            return QValidator.Invalid, string, pos

        self.editor.resetSelectionItems()

        if not len(string):
            return QValidator.Intermediate, string, pos

        for i in range(len(string)):
            sym = string[i]
            if validsymbols.find(sym) < 0:
                 return QValidator.Invalid, string, i

        words = string.split()
        if len(words) != 2:
            self.sendError("Only two LinkPoints allowed")
            return QValidator.Intermediate, string, pos

        if words[0] == words[1]:
            self.sendError("LinkPoints is equal")
            return QValidator.Intermediate, string, pos

        linkPoints = []
        warning = False
        for w in words:
            itemId = int(w)
            item = self.editor.itemById(itemId)
            if not item:
                self.sendError("Item id:%d is not exist" % itemId)
                return QValidator.Intermediate, string, pos

            if item.type() != LINK_TYPE:
                self.sendError("Item id:%d is not LinkPoint" % itemId)
                return QValidator.Intermediate, string, pos
            linkPoint = item
            linkPoints.append(linkPoint)

            conn = self.editor.connectionByLinkPoint(linkPoint)
            if conn:
                warning = True
                self.sendOkMessage("LinkPoint id:%d already in connection %d" %
                                    (linkPoint.id(), conn.id()))


        if not warning:
            self.sendOkMessage("OK")

        self.editor.itemsAddToSelection(linkPoints)
        return QValidator.Acceptable, string, pos



class IntValidator(DialogLineEditValidator):
    def __init__(self, editor, range=None):
        DialogLineEditValidator.__init__(self, editor)
        QIntValidator.__init__(self)
        self._range = range


    def validate(self, string, pos):
        validsymbols = "0123456789"
        string = str(string)
        if not self.stringIsValid(string):
            return QValidator.Invalid, string, pos

        if not len(string):
            return QValidator.Intermediate, string, pos

        enteredInt = int(string)
        for i in self._range:
            if i == enteredInt:
                self.sendOkMessage("OK")
                return QValidator.Acceptable, string, pos

        self.sendError("Incorrect number")
        return QValidator.Intermediate, string, pos




