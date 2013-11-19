'''
The MIT License (MIT)

Copyright (c) 2013 SinnerSchrader Mobile GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import datetime, time, os

class ObjectiveCCodeGenerator :

    projectPrefix = ""
    dirPath = ""
    
    def __init__(self):
        projectPrefix = ""
        dirPath = "classes"
    
    
    def getCommonDescriptionString(self) :
        today = datetime.date.fromtimestamp(time.time())
        commonDescription = "//\n//  Created by MetaJSONParser."
        commonDescription += "\n//  Copyright (c) "+  str(today.year) +" SinnerSchrader Mobile. All rights reserved.\n\n"
        return commonDescription
    
    def getHeaderDescriptionString(self, name) :
        hDescriptionString = "//\n//  "+ self.getTitledString(name) +".h\n"
        hDescriptionString += self.getCommonDescriptionString()
        return hDescriptionString
    
    def getSourceDescriptionString(self, name) :
        mDescriptionString = "//\n//  "+ self.getTitledString(name) +".m\n"
        mDescriptionString += self.getCommonDescriptionString()
        return mDescriptionString
    
    def makeVarName(self,schemeObj) :
        returnName = schemeObj.type_name
        if str(schemeObj.type_name) == "id" or str(schemeObj.type_name) == "description" :
            titleName = schemeObj.type_name.upper()
            titleName = titleName[:1] + schemeObj.type_name[1:]
            returnName = self.projectPrefix.lower() + titleName
        else :
            prefixes = ["new", "alloc", "copy"]
            for prefix in prefixes:
                if schemeObj.type_name.startswith(prefix):
                    titleName = schemeObj.type_name.upper()
                    titleName = titleName[:1] + schemeObj.type_name[1:]
                    returnName = self.projectPrefix.lower() + titleName
                    #print returnName
                    break
    
        return returnName
    
    def make(self, schemeObj) :
        headerString = ""
        sourceString = ""
    
        hDescriptionString = self.getHeaderDescriptionString(schemeObj.getMachineClassName())
        mDescriptionString = self.getSourceDescriptionString(schemeObj.getMachineClassName())

        hIncludeHeaders = "#import <Foundation/Foundation.h>\n"
        mIncludeHeaders = "#import \"" + self.projectPrefix + "APIParser.h\"\n"
        mIncludeHeaders += "#import \"NSString+RegExValidation.h\"\n"
        mIncludeHeaders += "#import \"" + schemeObj.getClassName() +".h\"\n"
        predefineCalsses = ""
        interfaceDefinition = "@class " + schemeObj.getClassName() + ";\n\n"
        interfaceDefinition += "@interface " + schemeObj.getMachineClassName()
        interfaceImplementation = "@implementation " + schemeObj.getMachineClassName() + "\n"
        propertyDefinition = ""
        methodDefinition = ""
        initMethodString = ""
        
        factoryMethodImpl = "\n+ (" + schemeObj.getClassName() +" *)" + self.makeVarName(schemeObj) + "WithDictionary:(NSDictionary *)dic withError:(NSError **)error {\n"
        factoryMethodImpl += "    return [[" + schemeObj.getClassName() + " alloc] initWithDictionary:dic withError:error];\n"
        factoryMethodImpl += "}\n\n"
        
        descriptionMethodString = "- (NSString *)description {\n    return [NSString stringWithFormat:@\"%@\",[self propertyDictionary]];\n}\n"
        propertyDictionaryString = "- (NSDictionary *)propertyDictionary {\n"
        
        encodeMethodString = "- (void)encodeWithCoder:(NSCoder*)coder {\n"
        decodeMethodString = "- (id)initWithCoder:(NSCoder *)coder {\n"
        
        """
            check base type
        """
        if schemeObj.isNaturalType() or schemeObj.rootBaseType() == "any":
            print "error : ", schemeObj.base_type ," (" , schemeObj.type_name, ") is natural type. Cannot make source code for it.\n"
            return False
        if schemeObj.rootBaseType() != "object" :
            print "error : ", schemeObj.base_type ," (" , schemeObj.type_name,") is not custom 'object' type.\n"
            return False
                
        if len(schemeObj.props) == 0 :
            # don't make source codes.
            print "NO Property : " + schemeObj.getMachineClassName()

        if schemeObj.base_type != "object" :

            encodeMethodString += "    [super encodeWithCoder:coder];\n"
            decodeMethodString += "    self = [super initWithCoder:coder];\n"
            propertyDictionaryString += "    NSDictionary *parentDic = [super propertyDictionary];\n"
            propertyDictionaryString += "    NSMutableDictionary *dic = [[NSMutableDictionary alloc] initWithDictionary:parentDic];\n"
            
            #print "(make : !object) : find scheme : " + schemeObj.base_type + " from : " + schemeObj.type_name
            if schemeObj.hasScheme(schemeObj.base_type) :
                parentSchemeObj = schemeObj.getScheme(schemeObj.base_type)
                hIncludeHeaders += "#import \"" + parentSchemeObj.getClassName() + ".h\"\n"
                interfaceDefinition += " : " + parentSchemeObj.getClassName() + "\n"
                initMethodString = "- (id)initWithDictionary:(NSDictionary *)dic  withError:(NSError **)error {\n    self = [super initWithDictionary:dic withError:error];\n"
            else :
                print "error : ", schemeObj.base_type, "(parent type of ", schemeObj.type_name ,") is not defined.\n"
                return False
        else :
            decodeMethodString += "    self = [super init];\n"
            interfaceDefinition += " : NSObject <NSCoding>\n"
            initMethodString = "- (id)initWithDictionary:(NSDictionary *)dic  withError:(NSError **)error {\n    self = [super init];\n"
            propertyDictionaryString += "    NSMutableDictionary *dic = [[NSMutableDictionary alloc] init];\n"

        initMethodString += "    if (self) {\n"
        interfaceDefinition += "\n"
        #factory method
        methodDefinition += "+ (" + schemeObj.getClassName() +" *)" + self.makeVarName(schemeObj) + "WithDictionary:(NSDictionary *)dic withError:(NSError **)error;\n"
        #initialize
        methodDefinition += "- (id)initWithDictionary:(NSDictionary *)dic withError:(NSError **)error;\n"
        #property dictionary method
        methodDefinition += "- (NSDictionary *)propertyDictionary;\n"
        getterMethodImplementation = ""
    
        
        """
            check properties
        """
        otherClasses = {}
        for propObj in schemeObj.props :
            if propObj.type_description and len(propObj.type_description) :
                propertyDefinition += "// " + propObj.type_description + "\n"
            propertyDefinition += self.propertyDefinitionString(propObj)

            decodeMethodString += self.propertyDecodeString(propObj, 1)
            encodeMethodString += self.propertyEncodeString(propObj, 1)
            propertyDictionaryString += self.setPropertyDictionaryString(propObj, "dic", 1)

            subTypeSchemeList = propObj.getSubType()
            if propObj.rootBaseType() == "array" and len(subTypeSchemeList) == 1 and not "any" in subTypeSchemeList:
                subTypeSchemeName = subTypeSchemeList[0]
                tmpArrayName = "tmp" + self.getTitledString(propObj.type_name) + "Array"
                initMethodString += self.getNaturalTypeGetterFromDictionaryCode(propObj, "NSArray *", tmpArrayName, "dic", propObj.type_name, (propObj.required != True), 2, "self")
                initMethodString += self.getNaturalTypeValidationCode(propObj, tmpArrayName, 2, "self")
                tmpMutableArrayName = "tmp" + self.getTitledString(propObj.type_name)
                initMethodString += "        NSMutableArray *" + tmpMutableArrayName + " = [[NSMutableArray alloc] initWithCapacity:" + tmpArrayName + ".count];\n"
                
                initMethodString += "        for (NSUInteger loop = 0; loop < " + tmpArrayName + ".count; loop++) {\n"
                subTypeSchemeObj = propObj.getScheme(subTypeSchemeName)

                if subTypeSchemeName in propObj.naturalTypeList :
                    initMethodString += self.getNaturalTypeGetterFromArrayCode(subTypeSchemeName, self.getNaturalTypeClassString(subTypeSchemeName), "tmpValue", tmpArrayName, "loop", (propObj.required != True), 3, "self")
                    initMethodString += "            if (tmpValue) {\n"
                    initMethodString += "                [" + tmpMutableArrayName + " addObject:tmpValue];\n"
                    initMethodString += "            }\n"
                elif subTypeSchemeObj and subTypeSchemeObj.isNaturalType() :
                    if subTypeSchemeObj :
                        initMethodString += self.getNaturalTypeGetterFromArrayCode(subTypeSchemeObj, self.getNaturalTypeClassString(subTypeSchemeObj.rootBaseType()), "tmpValue", tmpArrayName, "loop", (propObj.required != True), 3, "self")
                        initMethodString += self.getNaturalTypeValidationCode(subTypeSchemeObj, "tmpValue", 3, "self")
                    else :
                        initMethodString += self.getNaturalTypeGetterFromArrayCode(subTypeSchemeName, self.getNaturalTypeClassString(subTypeSchemeObj.rootBaseType()), "tmpValue", tmpArrayName, "loop", (propObj.required != True), 3, "self")
                    initMethodString += "            if (tmpValue) {\n"
                    initMethodString += "                [" + tmpMutableArrayName + " addObject:tmpValue];\n"
                    initMethodString += "            }\n"
                elif subTypeSchemeObj and subTypeSchemeObj.rootBaseType() == "object" :
                    tmpDicName = "tmpDic"
                    initMethodString += self.getDictionaryGetterFromArrayCode(tmpDicName, tmpArrayName, "loop", False, 3, "self")
                    initMethodString += "            " + subTypeSchemeObj.getClassName() + "*tmpObject = nil;\n"
                    initMethodString += self.getObjectAllocatorFromDictionaryCode(False, subTypeSchemeObj.getClassName(), "tmpObject", tmpDicName, (propObj.required != True), 3, "self")
                    initMethodString += "            if (tmpObject) {\n"
                    initMethodString += "                [" + tmpMutableArrayName + " addObject:tmpObject];\n"
                    initMethodString += "            }\n"
                else :
                    print "Error : can't handle subType of " + propObj.type_name
                    return False

                initMethodString += "        }\n"
                initMethodString += "        self." + self.makeVarName(propObj) + " = [NSArray arrayWithArray:" + tmpMutableArrayName + "];\n"
        
            elif propObj.isNaturalType() :
                initMethodString += self.getNaturalTypeGetterFromDictionaryCode(propObj, "", "self." + self.makeVarName(propObj), "dic", propObj.type_name, (propObj.required != True), 2, "self")
                initMethodString += self.getNaturalTypeValidationCode(propObj, "self." + self.makeVarName(propObj), 2, "self")
                if len(subTypeSchemeList) > 1 or "any" in subTypeSchemeList :
                    pass
                else :
                    continue
        
            elif propObj.rootBaseType() == "object" :
                if otherClasses.has_key(propObj.type_name) == False :
                    otherClasses[propObj.type_name] =  propObj
                tmpVarName = "tmp"+self.getTitledString(propObj.type_name)
                initMethodString += self.getDictionaryGetterFromDictionaryCode(tmpVarName, "dic", propObj.type_name, (propObj.required != True), 2, "self")
                initMethodString += self.getObjectAllocatorFromDictionaryCode(False, propObj.getClassName(), "self." + self.makeVarName(propObj), tmpVarName, (propObj.required != True), 2, "self")
                continue

            else :
                tmpVarName = "tmp" + self.getTitledString(propObj.type_name)
                initMethodString += self.getGetterFromDictionaryCode("id ", tmpVarName, "dic", propObj.type_name, (propObj.required != True), 2, "self")
                initMethodString += "        if ("+ tmpVarName +") {\n"
                initMethodString += self.getDictionaryAllocatorCode(False, "self." + self.makeVarName(propObj), tmpVarName, propObj.type_name, 3, "self")
                initMethodString += "        }\n"

            if propObj.rootBaseType() == "array" and len(subTypeSchemeList) == 1 and not "any" in subTypeSchemeList:
                pass
            else :
                for methodDefinitionString in self.getterMethodDefinitionString(propObj) :
                    methodDefinition += methodDefinitionString
                getterMethodImplementation += self.getterMethodString(propObj);

            if propObj.rootBaseType() == "multi" :
                for multiTypeScheme in propObj.getBaseTypes() :
                    if multiTypeScheme in propObj.naturalTypeList or multiTypeScheme == "any" :
                        continue
                    #print "(make : property multi) : find scheme : " + multiTypeScheme + " from : " + propObj.type_name
                    elif schemeObj.hasScheme(multiTypeScheme) == False :
                        print "Warning : " + propObj.type_name + " in " + propObj.getDomainString() + " (multi) has undefined base-type."
                        print "          undefined type : " + multiTypeScheme
                        continue
                    multiTypeSchemeObj = propObj.getScheme(multiTypeScheme)
                
                    if multiTypeSchemeObj.rootBaseType() == "object" and otherClasses.has_key(multiTypeScheme) == False:
                        otherClasses[multiTypeScheme] =  multiTypeSchemeObj
            elif propObj.rootBaseType() == "any" :
                pass

            elif propObj.rootBaseType() == "array" :
                for subTypeScheme in propObj.getSubType() :
                    if subTypeScheme in propObj.naturalTypeList or subTypeScheme == "any" :
                        continue
                    #print "(make : property array) : find scheme : " + subTypeScheme + " from : " + propObj.type_name
                    elif propObj.hasScheme(subTypeScheme) == False:
                        print "Warning : " + propObj.type_name + " in " + propObj.getDomainString() + " (array) has undefined sub type."
                        print "          undefined type : " + multiTypeScheme
                        continue
                    subTypeSchemeObj = propObj.getScheme(subTypeScheme)
                    if subTypeSchemeObj.rootBaseType() == "object" and otherClasses.has_key(subTypeSchemeObj.type_name) == False :
                        otherClasses[subTypeSchemeObj.type_name] =  subTypeSchemeObj

        encodeMethodString += "}\n"
        decodeMethodString += "    return self;\n}\n"
        propertyDictionaryString += "    return dic;\n}\n"
        otherClassNameList = []
        otherClassList = []
        for otherClassName in otherClasses :
            otherClassObject = otherClasses[otherClassName]
            if not otherClassObject.getClassName() in otherClassNameList :
                otherClassList.append(otherClassObject)
                otherClassNameList.append(otherClassObject.getClassName())

        for includeTypeObj in otherClassList :
            predefineCalsses += "@class " + includeTypeObj.getClassName() + ";\n"
            mIncludeHeaders += "#import \""+ includeTypeObj.getClassName() + ".h\"\n"
            if len(includeTypeObj.props) and includeTypeObj.rootBaseType() == "object" :
                self.make(includeTypeObj)

        initMethodString += "    }\n" + "    return self;\n}\n\n"
        interfaceDefinition += "\n" + propertyDefinition + "\n" + methodDefinition + "\n@end\n"

        interfaceImplementation += "\n#pragma mark - factory\n" + factoryMethodImpl
        interfaceImplementation += "\n#pragma mark - initialize\n" + initMethodString
        interfaceImplementation += "\n#pragma mark - getter\n" + getterMethodImplementation
        interfaceImplementation += "\n#pragma mark - NSCoding\n" + encodeMethodString + decodeMethodString
        interfaceImplementation += "\n#pragma mark - Object Info\n" + propertyDictionaryString + descriptionMethodString +"\n@end\n"
        headerString += hDescriptionString + hIncludeHeaders + "\n"

        if len(predefineCalsses) > 0 :
            headerString += predefineCalsses + "\n"

        headerString += interfaceDefinition + "\n"
        sourceString += mDescriptionString + mIncludeHeaders + "\n\n" + interfaceImplementation

        if not os.path.exists(self.dirPath):
            os.makedirs(self.dirPath)

        if self.dirPath.endswith("/") :
            self.dirPath = self.dirPath[:-1]

        if not os.path.exists(self.dirPath + "/AbstractInterfaceFiles/"):
            os.makedirs(self.dirPath + "/AbstractInterfaceFiles/")

        #machine file
        #print headerString
        try:
            headerFile = open(self.dirPath + "/AbstractInterfaceFiles/" + schemeObj.getMachineClassName() + ".h", "w")
            print "create " + self.dirPath + "/AbstractInterfaceFiles/" + schemeObj.getMachineClassName() + ".h" + " file..."
            headerFile.write(headerString) # Write a string to a file
        finally :
            headerFile.close()

        #print sourceString
        try:
            sourceFile = open(self.dirPath + "/AbstractInterfaceFiles/" + schemeObj.getMachineClassName() + ".m", "w")
            print "create " + self.dirPath + "/AbstractInterfaceFiles/" + schemeObj.getMachineClassName() + ".m" + " file..."
            sourceFile.write(sourceString) # Write a string to a file
        finally :
            sourceFile.close()

        
        #customizable file 
        customizableInterface = self.getHeaderDescriptionString(schemeObj.getClassName())
        customizableInterface += "#import \"" + schemeObj.getMachineClassName() +".h\"\n"
        customizableInterface += "@interface " + schemeObj.getClassName() + " : " + schemeObj.getMachineClassName() + "\n\n@end\n\n"

        customizableImplementation = self.getSourceDescriptionString(schemeObj.getClassName())
        customizableImplementation += "#import \"" + schemeObj.getClassName() +".h\"\n"
        customizableImplementation += "@implementation " + schemeObj.getClassName() + "\n\n@end\n\n"
        

        #print headerString
        customizableInterfaceFileName = self.dirPath + "/" + schemeObj.getClassName() + ".h"
        if os.path.isfile(customizableInterfaceFileName) is False :
            print "create " + customizableInterfaceFileName + " file..."
            try:
                headerFile = open(customizableInterfaceFileName, "w")
                headerFile.write(customizableInterface) # Write a string to a file
            finally :
                headerFile.close()

        #print sourceString
        customizableImplementationFileName = self.dirPath + "/" + schemeObj.getClassName() + ".m"
        if os.path.isfile(customizableImplementationFileName) is False :
            print "create " + customizableImplementationFileName + " file..."
            try:
                sourceFile = open(customizableImplementationFileName, "w")
                sourceFile.write(customizableImplementation) # Write a string to a file
            finally :
                sourceFile.close()

        return True


    """
    getter method
    """
    def getterMethodDefinitionStringInDictionary(self, returnTypeName, typeName, typeTitle, postFix) :
        return "- (" + returnTypeName + ")" + typeName + "As" + typeTitle + postFix
    
    def getterMethodDefinitionStringInArray(self, returnTypeName, typeName, arrayName, postFix) :
        return "- (" + returnTypeName + ")" + typeName + "In"+  arrayName + postFix
    
    def getTitledString(self, inputString) :
        titledString = inputString.upper()
        titledString = titledString[:1] + inputString[1:]
        return titledString

    def getNaturalTypeClassTitleString(self,typeName) :
        titleString = self.getTitledString(typeName)
        if typeName == "boolean" or typeName == "string" or typeName == "date" or typeName == "data" or typeName == "number" or typeName == "array" :
            return titleString
        else :
            return "Object"

    def getNaturalTypeClassString(self,typeName) :
        if typeName == "boolean" :
            return "BOOL "
        elif typeName == "string" :
            return "NSString *"
        elif typeName == "date" :
            return "NSDate *"
        elif typeName == "data" :
            return "NSData *"
        elif typeName == "number" :
            return "NSNumber *"
        elif typeName == "array" :
            return "NSArray *"
        else :
            return "id "

    def getterMethodDefinitionString(self, schemeObj) :
        resultStringList= []
        
        titleName = schemeObj.type_name.upper()
        titleName = titleName[:1] + schemeObj.type_name[1:]
        postFix = ":(NSError **)error;\n"

        if schemeObj.rootBaseType() == "multi" :
            for schemeName in schemeObj.getBaseTypes() :
                #print "(getterMethodDefinitionString : multi) : find scheme : " + schemeName + " from : " + schemeObj.type_name
                if schemeObj.hasScheme(schemeName) :
                    baseSubTypeSchemeObj = schemeObj.getScheme(schemeName)
                    baseSubTypeTitle = baseSubTypeSchemeObj.type_name.upper()
                    baseSubTypeTitle = baseSubTypeTitle[:1] + baseSubTypeSchemeObj.type_name[1:]
                    
                    if baseSubTypeSchemeObj.isNaturalType() == False :
                        resultStringList.append(self.getterMethodDefinitionStringInDictionary(baseSubTypeSchemeObj.getClassName() + " *", schemeObj.type_name, baseSubTypeSchemeObj.getClassName(), postFix))
                    else :
                        resultStringList.append(self.getterMethodDefinitionStringInDictionary(self.getNaturalTypeClassString(baseSubTypeSchemeObj.rootBaseType()), schemeObj.type_name, baseSubTypeTitle, postFix))
            
                elif schemeName == "any" :
                    resultStringList.append(self.getterMethodDefinitionStringInDictionary("id", schemeObj.type_name, "Object", postFix))
                else :
                    resultStringList.append(self.getterMethodDefinitionStringInDictionary(self.getNaturalTypeClassString(schemeName), schemeObj.type_name, self.getNaturalTypeClassTitleString(schemeName),postFix))

        elif schemeObj.rootBaseType() == "array" :
            postFix = "AtIndex:(NSUInteger)index withError:(NSError **)error;\n";
            for schemeName in schemeObj.getSubType() :
                #print "(getterMethodDefinitionString : array) : find scheme : " + schemeName + " from : " + schemeObj.type_name
                if schemeObj.hasScheme(schemeName) :
                    baseSubTypeSchemeObj = schemeObj.getScheme(schemeName)
                    
                    if baseSubTypeSchemeObj.isNaturalType() == False :
                        resultStringList.append(self.getterMethodDefinitionStringInArray(baseSubTypeSchemeObj.getClassName() + " *", baseSubTypeSchemeObj.type_name, titleName, postFix))
                    else :
                        resultStringList.append(self.getterMethodDefinitionStringInArray(self.getNaturalTypeClassString(baseSubTypeSchemeObj.rootBaseType()), baseSubTypeSchemeObj.type_name, titleName, postFix))
            
                elif schemeName == "any" :
                    resultStringList.append(self.getterMethodDefinitionStringInArray("id", "object", titleName, postFix))
                else :
                    resultStringList.append(self.getterMethodDefinitionStringInArray(self.getNaturalTypeClassString(schemeName), schemeName, titleName, postFix))

        elif schemeObj.base_type == "any"  :
            resultStringList.append(self.getterMethodDefinitionStringInDictionary("id", schemeObj.type_name, "Object", postFix))

        elif schemeObj.isNaturalType() :
            print "Error : " + schemeObj.type_name + " is Natural type. don't need to define getter method.\n"
            resultStringList = []

        else :
            print "Error : " + schemeObj.type_name + " is Custom Object type. don't need to define getter method.\n"
            resultStringList = []

        return resultStringList
            
    def getterMethodString(self, schemeObj) :
        resultString = ""
        postFix = ":(NSError **)error {\n"
        titleName = schemeObj.type_name.upper()
        titleName = titleName[:1] + schemeObj.type_name[1:]
        tmpVarName = "tmp" + self.getTitledString(schemeObj.type_name)
        selfDicName = "self." + self.makeVarName(schemeObj)
        
        if schemeObj.rootBaseType() == "multi" :
            for schemeName in schemeObj.getBaseTypes() :
                #print "(getterMethodString : multi) : find scheme : " + schemeName + " from : " + schemeObj.type_name
                if schemeObj.hasScheme(schemeName) :
                    baseSubTypeSchemeObj = schemeObj.getScheme(schemeName)
                    baseSubTypeTitle = baseSubTypeSchemeObj.type_name.upper()
                    baseSubTypeTitle = baseSubTypeTitle[:1] + baseSubTypeSchemeObj.type_name[1:]
                    
                    if baseSubTypeSchemeObj.isNaturalType() == False :
                        tmpDicName = "tmp" + self.getTitledString(schemeObj.type_name) + "Dic"
                        resultString += self.getterMethodDefinitionStringInDictionary(baseSubTypeSchemeObj.getClassName() + " *", schemeObj.type_name, baseSubTypeSchemeObj.getClassName(), postFix)
                        resultString += self.getDictionaryGetterFromDictionaryCode(tmpDicName, selfDicName, schemeObj.type_name, (schemeObj.required != True), 1, "nil")
                        resultString += self.getHandleErrorCode( tmpDicName +" == nil", "", "nil", 1)
                        resultString += "    " + baseSubTypeSchemeObj.getClassName() + " *" + tmpVarName + " = nil;\n"
                        resultString += self.getObjectAllocatorFromDictionaryCode(False, baseSubTypeSchemeObj.getClassName(), tmpVarName, tmpDicName, (schemeObj.required != True), 1, "nil")
                        resultString += "    return " + tmpVarName + ";\n}\n"
                    else :
                        resultString += self.getterMethodDefinitionStringInDictionary(self.getNaturalTypeClassString(baseSubTypeSchemeObj.rootBaseType()), schemeObj.type_name, baseSubTypeTitle, postFix)
                        resultString += self.getNaturalTypeGetterFromDictionaryCode(baseSubTypeSchemeObj, self.getNaturalTypeClassString(baseSubTypeSchemeObj.rootBaseType()), tmpVarName, selfDicName, schemeObj.type_name, (schemeObj.required != True), 1, "nil")
                        resultString += self.getHandleErrorCode( tmpVarName +" == nil", "", "nil", 1)
                        resultString += self.getNaturalTypeValidationCode(baseSubTypeSchemeObj, tmpVarName, 1, "nil")
                        resultString += "    return " + tmpVarName + ";\n}\n"
                
                elif schemeName == "any" :
                    resultString += self.getterMethodDefinitionStringInDictionary("id", schemeObj.type_name, "Object", postFix)
                    resultString += self.getUndefinedTypeGetterFromDictionaryCode("id ", tmpVarName, selfDicName, schemeObj.type_name, (schemeObj.required != True), 1, "nil")
                    resultString += "    return " + tmpVarName + ";\n}\n"
                else :
                    resultString += self.getterMethodDefinitionStringInDictionary(self.getNaturalTypeClassString(schemeName), schemeObj.type_name, self.getNaturalTypeClassTitleString(schemeName),postFix)
                    resultString += self.getNaturalTypeGetterFromDictionaryCode(schemeName, self.getNaturalTypeClassString(schemeName), tmpVarName, selfDicName, schemeObj.type_name, (schemeObj.required != True), 1, "nil")
                    resultString += "    return " + tmpVarName + ";\n}\n"
        
        elif schemeObj.rootBaseType() == "array" :
            postFix = "AtIndex:(NSUInteger)index withError:(NSError **)error {\n";
            for schemeName in schemeObj.getSubType() :
                if schemeObj.hasScheme(schemeName) :
                    #print "(getterMethodString : array) : find scheme : " + schemeName + " from : " + schemeObj.type_name
                    baseSubTypeSchemeObj = schemeObj.getScheme(schemeName)
                    
                    if baseSubTypeSchemeObj.isNaturalType() == False :
                        tmpDicName = "tmp" + self.getTitledString(schemeObj.type_name) + "Dic"
                        resultString += self.getterMethodDefinitionStringInArray(baseSubTypeSchemeObj.getClassName() + " *", baseSubTypeSchemeObj.type_name, titleName, postFix)
                        resultString += self.getDictionaryGetterFromArrayCode(tmpDicName, selfDicName, "index", (schemeObj.required != True), 1, "nil")
                        resultString += "    " + baseSubTypeSchemeObj.getClassName() + " *" + tmpVarName + " = nil;\n"
                        resultString += self.getHandleErrorCode( tmpDicName +" == nil", "", "nil", 1)
                        resultString += self.getObjectAllocatorFromDictionaryCode(False, baseSubTypeSchemeObj.getClassName(), tmpVarName, tmpDicName, (schemeObj.required != True), 1, "nil")
                        resultString += "    return " + tmpVarName + ";\n}\n"

                    else :
                        resultString += self.getterMethodDefinitionStringInArray(self.getNaturalTypeClassString(baseSubTypeSchemeObj.rootBaseType()), baseSubTypeSchemeObj.type_name,titleName,postFix)
                        resultString += self.getNaturalTypeGetterFromArrayCode(baseSubTypeSchemeObj, self.getNaturalTypeClassString(baseSubTypeSchemeObj.rootBaseType()), tmpVarName, selfDicName, "index", (schemeObj.required != True), 1, "nil")
                        resultString += self.getNaturalTypeValidationCode(baseSubTypeSchemeObj, tmpVarName, 1, "nil")
                        resultString += "    return " + tmpVarName + ";\n}\n"

            
                elif schemeName == "any" :
                    resultString += self.getterMethodDefinitionStringInArray("id", "object", titleName, postFix)
                    resultString += self.getGetterFromArrayCode("id ", tmpVarName, selfDicName, "index", (schemeObj.required != True), 1, "nil")
                    resultString += "    return " + tmpVarName + ";\n}\n"
                else :
                    resultString += self.getterMethodDefinitionStringInArray(self.getNaturalTypeClassString(schemeName), schemeName, titleName, postFix)
                    resultString += self.getNaturalTypeGetterFromArrayCode(schemeName, self.getNaturalTypeClassString(schemeName), tmpVarName, selfDicName, "index", (schemeObj.required != True), 1, "nil")
                    resultString += "    return " + tmpVarName + ";\n}\n"
        
        elif schemeObj.base_type == "any"  :
            resultString += self.getterMethodDefinitionStringInDictionary("id", schemeObj.type_name, "Object", postFix)
            resultString += self.getUndefinedTypeGetterFromDictionaryCode("id ", tmpVarName, selfDicName, schemeObj.type_name, (schemeObj.required != True), 1, "nil")
            resultString += "    return " + tmpVarName + ";\n}\n"
        
        elif schemeObj.isNaturalType() :
            print "Error : " + schemeObj.type_name + " is Natural type. don't need to implement getter method.\n"
            return "#error " + schemeObj.type_name + " is Natural type. don't need to implement getter method.\n"
        
        else :
            print "Error : " + schemeObj.type_name + " is Custom Object type. don't need to implement getter method.\n"
            return "#error " + schemeObj.type_name + " is Custom Object type. don't need to implement getter method.\n"
    
        return resultString
    
    def getIndentString(self, indentDepth) :
        resultString = ""
        indentString = "    "
        for loop in range(indentDepth) :
            resultString += indentString

        return resultString
    
    def getHandleErrorCode(self, statement, errorString, returnVarName, indentDepth) :
        resultString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth+1)
        resultString += firstIndent + "if ("+ statement + ") {\n"
        if len(errorString) :
            resultString += secondIndent + errorString
        resultString += secondIndent + "return " + returnVarName + ";\n" + firstIndent + "}\n"
        return  resultString

    def getStringValidationCode(self, schemeObj, varName, indentDepth, returnVarName) :
        resultString = ""
        statementString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth+1)
        errorString = "NSDictionary *userInfo = [NSDictionary dictionaryWithObjectsAndKeys:@\"" + self.makeVarName(schemeObj) + "\", @\"propertyName\", @\"" + schemeObj.type_name + "\", @\"key\", @\"validation error\", @\"reason\", NSStringFromClass([self class]), @\"objectClass\",nil];\n"
        errorString += secondIndent + "*error = [NSError errorWithDomain:k" + self.projectPrefix + "ErrorDomain_parser code:k" + self.projectPrefix + "ErrorDomain_parser_valueIsNotValid userInfo:userInfo];\n"
        errorString += secondIndent + "NSLog(@\"%@\", *error);\n"
        
        maxResult = schemeObj.getMaxLength()
        
        if maxResult[0] :
            statementString = str(varName) + ".length > " + str(maxResult[1])
            resultString += self.getHandleErrorCode(statementString, errorString, returnVarName, indentDepth)
        
        minResult = schemeObj.getMinLength()
        if minResult[0] :
            statementString = varName + ".length < " + str(minResult[1])
            resultString += self.getHandleErrorCode(statementString, errorString, returnVarName, indentDepth)

        regExResult = schemeObj.getRegex()
        if regExResult[0] :
            statementString = varName + " && ["+varName+" matchesRegExString:@\"" +str(regExResult[1])+ "\"] == NO"
            resultString += self.getHandleErrorCode(statementString, errorString, returnVarName, indentDepth)
            
        return resultString

    def getDateValidationCode(self, schemeObj, varName, indentDepth, returnVarName) :
        resultString = ""
        statementString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth+1)
        errorString = "NSDictionary *userInfo = [NSDictionary dictionaryWithObjectsAndKeys:@\"" + self.makeVarName(schemeObj) + "\", @\"propertyName\", @\"" + schemeObj.type_name + "\", @\"key\", @\"validation error\", @\"reason\", NSStringFromClass([self class]), @\"objectClass\",nil];\n"
        errorString += secondIndent + "*error = [NSError errorWithDomain:k" + self.projectPrefix + "ErrorDomain_parser code:k" + self.projectPrefix + "ErrorDomain_parser_valueIsNotValid userInfo:userInfo];\n"
        errorString += secondIndent + "NSLog(@\"%@\", *error);\n"
        
        maxResult = schemeObj.getMaxValue()
        if maxResult[0] :
            statementString = "["+varName+" timeIntervalSince1970] > " + str(maxResult[1])
            resultString += self.getHandleErrorCode(statementString, errorString, returnVarName, indentDepth)
        
        minResult = schemeObj.getMinValue()
        if minResult[0] :
            statementString = "["+varName+" timeIntervalSince1970] < " + str(minResult[1])
            resultString += self.getHandleErrorCode(statementString, errorString, returnVarName, indentDepth)

        return resultString

    def getDataValidationCode(self, schemeObj, varName, indentDepth, returnVarName) :
        resultString = ""
        statementString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth+1)
        errorString = "NSDictionary *userInfo = [NSDictionary dictionaryWithObjectsAndKeys:@\"" + self.makeVarName(schemeObj) + "\", @\"propertyName\", @\"" + schemeObj.type_name + "\", @\"key\", @\"validation error\", @\"reason\", NSStringFromClass([self class]), @\"objectClass\",nil];\n"
        errorString += secondIndent + "*error = [NSError errorWithDomain:k" + self.projectPrefix + "ErrorDomain_parser code:k" + self.projectPrefix + "ErrorDomain_parser_valueIsNotValid userInfo:userInfo];\n"
        errorString += secondIndent + "NSLog(@\"%@\", *error);\n"
        
        maxResult = schemeObj.getMaxLength()
        if maxResult[0] :
            statementString = varName+".length > " + str(maxResult[1])
            resultString += self.getHandleErrorCode(statementString, errorString, returnVarName, indentDepth)
        
        minResult = schemeObj.getMinLength()
        if minResult[0] :
            statementString = varName+".length < " + str(minResult[1])
            resultString += self.getHandleErrorCode(statementString, errorString, returnVarName, indentDepth)

        return resultString

    def getNumberValidationCode(self, schemeObj, varName, indentDepth, returnVarName) :
        resultString = ""
        statementString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth+1)
        errorString = "NSDictionary *userInfo = [NSDictionary dictionaryWithObjectsAndKeys:@\"" + self.makeVarName(schemeObj) + "\", @\"propertyName\", @\"" + schemeObj.type_name + "\", @\"key\", @\"validation error\", @\"reason\", NSStringFromClass([self class]), @\"objectClass\",nil];\n"
        errorString += secondIndent + "*error = [NSError errorWithDomain:k" + self.projectPrefix + "ErrorDomain_parser code:k" + self.projectPrefix + "ErrorDomain_parser_valueIsNotValid userInfo:userInfo];\n"
        errorString += secondIndent + "NSLog(@\"%@\", *error);\n"
        
        maxResult = schemeObj.getMaxValue()
        if maxResult[0] :
            statementString = "["+varName+" floatValue] > " + str(maxResult[1])
            resultString += self.getHandleErrorCode(statementString, errorString, returnVarName, indentDepth)
        
        minResult = schemeObj.getMinValue()
        if minResult[0] :
            statementString = "["+varName+" floatValue] < " + str(minResult[1])
            resultString += self.getHandleErrorCode(statementString, errorString, returnVarName, indentDepth)
        return resultString
            
    def getArrayValidationCode(self, schemeObj, varName, indentDepth, returnVarName) :
        resultString = ""
        statementString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth+1)
        errorString = "NSDictionary *userInfo = [NSDictionary dictionaryWithObjectsAndKeys:@\"" + self.makeVarName(schemeObj) + "\", @\"propertyName\", @\"" + schemeObj.type_name + "\", @\"key\", @\"validation error\", @\"reason\", NSStringFromClass([self class]), @\"objectClass\",nil];\n"
        errorString += secondIndent + "*error = [NSError errorWithDomain:k" + self.projectPrefix + "ErrorDomain_parser code:k" + self.projectPrefix + "ErrorDomain_parser_valueIsNotValid userInfo:userInfo];\n"
        errorString += secondIndent + "NSLog(@\"%@\", *error);\n"
                
        maxResult = schemeObj.getMaxCount()
        if maxResult[0] :
            statementString = varName+".count > " + str(maxResult[1])
            resultString += self.getHandleErrorCode(statementString, errorString, returnVarName, indentDepth)
        
        minResult = schemeObj.getMinCount()
        if minResult[0] :
            statementString = varName+".count < " + str(minResult[1])
            resultString += self.getHandleErrorCode(statementString, errorString, returnVarName, indentDepth)

        return resultString

    def getNaturalTypeValidationCode(self, schemeObj, varName, indentDepth, returnVarName) :
        if schemeObj.isNaturalType() :
            if schemeObj.rootBaseType() == "array" :
                return self.getArrayValidationCode(schemeObj, varName, indentDepth, returnVarName)
            elif schemeObj.rootBaseType() == "string" :
                return self.getStringValidationCode(schemeObj, varName, indentDepth, returnVarName)
            elif schemeObj.rootBaseType() == "number" :
                return self.getNumberValidationCode(schemeObj, varName, indentDepth, returnVarName)
            elif schemeObj.rootBaseType() == "date" :
                return self.getDateValidationCode(schemeObj, varName, indentDepth, returnVarName)
            elif schemeObj.rootBaseType() == "data" :
                return self.getDataValidationCode(schemeObj, varName, indentDepth, returnVarName)
    
        return ""


    def getNaturalTypeGetterFromDictionaryCode(self, schemeObj, className, varName, dicName, keyName, allowNull, indentDepth, returnVarName) :
        schemeBaseType = ""
        if type(schemeObj) == str or type(schemeObj) == unicode:
            schemeBaseType = str(schemeObj)
        elif schemeObj.isNaturalType() :
            schemeBaseType = str(schemeObj.rootBaseType())
        else :
            print "Error (getNaturalTypeGetterFromDictionaryCode): undfined scheme base type " + schemeObj
            return "#error - undfined scheme base type\n"
        resultString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth+1)

        if schemeBaseType == "array" :
            resultString += firstIndent + className + varName + " = [" + self.projectPrefix + "APIParser arrayFromResponseDictionary:" + dicName + " forKey:@\"" + keyName + "\" acceptNil:"
        elif schemeBaseType == "string" :
            resultString += firstIndent + className + varName + " = [" + self.projectPrefix + "APIParser stringFromResponseDictionary:" + dicName + " forKey:@\"" + keyName + "\" acceptNumber:NO acceptNil:"
        elif schemeBaseType == "number" :
            resultString += firstIndent + className + varName + " = [" + self.projectPrefix + "APIParser numberFromResponseDictionary:" + dicName + " forKey:@\"" + keyName + "\" acceptNil:"
        elif schemeBaseType == "date" :
            dateObjSubType = schemeObj.getSubType()
            if len(dateObjSubType) and dateObjSubType[0] == str("ms") :
                resultString += firstIndent + className + varName + " = [" + self.projectPrefix + "APIParser dateWithMilliSecondsTimeIntervalFromResponseDictionary:" + dicName + " forKey:@\"" + keyName + "\" acceptNil:"
            else :
                resultString += firstIndent + className + varName + " = [" + self.projectPrefix + "APIParser dateWithTimeIntervalFromResponseDictionary:" + dicName + " forKey:@\"" + keyName + "\" acceptNil:"
        elif schemeBaseType == "data" :
            resultString += firstIndent + className + varName + " = [" + self.projectPrefix + "APIParser dataFromResponseDictionary:" + dicName + " forKey:@\"" + keyName + "\" acceptNil:"
        elif schemeBaseType == "boolean" :
            resultString += firstIndent + className + varName + " = [" + self.projectPrefix + "APIParser boolFromResponseDictionary:" + dicName + " forKey:@\"" + keyName + "\" acceptNil:"
        else :
            print "Error (getNaturalTypeGetterFromDictionaryCode): undfined scheme natural base type " + schemeObj
            return "#error - undfined scheme natural base type\n"

        if allowNull :
            resultString += "YES"
        else :
            resultString += "NO"
        resultString += " error:error];\n"
        resultString += self.getHandleErrorCode("*error", "", returnVarName, indentDepth)

        return resultString

    def getUndefinedTypeGetterFromDictionaryCode(self, className, varName, dicName, keyName, allowNull, indentDepth, returnVarName) :
        resultString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth+1)
        
        resultString += firstIndent
        if className and len(className) :
            resultString += className
        resultString += varName + " = [" + self.projectPrefix + "APIParser objectFromResponseDictionary:" + dicName + " forKey:@\"" + keyName + "\" acceptNil:"
    
        if allowNull :
            resultString += "YES"
        else :
            resultString += "NO"
        resultString += " error:error];\n"
        resultString += self.getHandleErrorCode("*error", "", returnVarName, indentDepth)
        
        return resultString
                
    def getNaturalTypeGetterFromArrayCode(self, schemeObj, className, varName, arrayName, indexVar, allowNull, indentDepth, returnVarName) :
        schemeBaseType = ""
        if type(schemeObj) == str or type(schemeObj) == unicode:
            schemeBaseType = str(schemeObj)
        elif schemeObj.isNaturalType() :
            schemeBaseType = str(schemeObj.rootBaseType())
        else :
            print "Error (getNaturalTypeGetterFromArrayCode): undfined scheme base type " + schemeObj
            return "#error - undfined scheme base type\n"

        resultString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth+1)
        
        if schemeBaseType == "array" :
            resultString += firstIndent + className + varName + " = [" + self.projectPrefix + "APIParser arrayFromResponseArray:" + arrayName + " atIndex:" + indexVar + " acceptNil:"
        elif schemeBaseType == "string" :
            resultString += firstIndent + className + varName + " = [" + self.projectPrefix + "APIParser stringFromResponseArray:" + arrayName + " atIndex:" + indexVar + " acceptNil:"
        elif schemeBaseType == "number" :
            resultString += firstIndent + className + varName + " = [" + self.projectPrefix + "APIParser numberFromResponseArray:" + arrayName + " atIndex:" + indexVar + " acceptNil:"
        elif schemeBaseType == "date" :
            resultString += firstIndent + className + varName + " = [" + self.projectPrefix + "APIParser dateWithTimeIntervalFromResponseArray:" + arrayName + " atIndex:" + indexVar + " acceptNil:"
        elif schemeBaseType == "data" :
            resultString += firstIndent + className + varName + " = [" + self.projectPrefix + "APIParser dataFromResponseArray:" + arrayName + " atIndex:" + indexVar + " acceptNil:"
        elif schemeBaseType == "boolean" :
            resultString += firstIndent + className + varName + " = [" + self.projectPrefix + "APIParser boolFromResponseArray:" + arrayName + " atIndex:" + indexVar + " acceptNil:"
        else :
            print "Error (getNaturalTypeGetterFromArrayCode): undfined scheme natural base type " + schemeObj
            return "#error - undfined scheme natural base type\n"
            
        if allowNull :
            resultString += "YES"
        else :
            resultString += "NO"
        resultString += " error:error];\n"
        resultString += self.getHandleErrorCode("*error", "", returnVarName, indentDepth)
        
        return resultString
                
    def getDictionaryGetterFromDictionaryCode(self, varName, dicName, keyName, allowNull, indentDepth, returnVarName) :
        resultString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth+1)
        
        resultString += firstIndent + "NSDictionary *"+ varName + " = [" + self.projectPrefix + "APIParser dictionaryFromResponseDictionary:" + dicName + " forKey:@\"" + keyName + "\" acceptNil:"
        if allowNull :
            resultString += "YES"
        else :
            resultString += "NO"
        resultString += " error:error];\n"
        resultString += self.getHandleErrorCode("*error", "", returnVarName, indentDepth)
        return resultString

    def getDictionaryGetterFromArrayCode(self, varName, arrayName, indexVar, allowNull, indentDepth, returnVarName) :
        resultString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth+1)
    
        resultString += firstIndent + "NSDictionary *"+ varName + " = [" + self.projectPrefix + "APIParser dictionaryFromResponseArray:" + arrayName + " atIndex:" + indexVar + " acceptNil:"
        if allowNull :
            resultString += "YES"
        else :
            resultString += "NO"
        resultString += " error:error];\n"
        resultString += self.getHandleErrorCode("*error", "", returnVarName, indentDepth)
    
        return resultString

    def getObjectAllocatorFromDictionaryCode(self, defineClass, className, varName, dicName, allowNull, indentDepth, returnVarName) :
        resultString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth+1)
        resultString += firstIndent + "if (" + dicName + ") {\n"
        resultString += secondIndent
        if defineClass :
            resultString += className+ " *"
        resultString += varName + "= [[" + className + " alloc] initWithDictionary:" + dicName + " withError:error];\n"
        resultString += self.getHandleErrorCode("*error", "", returnVarName, indentDepth + 1)
        resultString += firstIndent + "}\n"

        return resultString
    
    def getDictionaryAllocatorCode(self, defineClass, varName, objectName, keyNmae, indentDepth, returnVarName) :
        resultString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth+1)
        
        resultString += firstIndent
        if defineClass :
            resultString += "NSDictionary *"
        resultString += varName + " = [NSDictionary dictionaryWithObjectsAndKeys:"+ objectName +", @\"" + keyNmae + "\", nil];\n"
        
        return resultString

    def getGetterFromDictionaryCode(self, className, varName, dicName, keyName, allowNull, indentDepth, returnVarName) :
        resultString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth+1)
        
        resultString += firstIndent + className + varName + " = [" + self.projectPrefix + "APIParser objectFromResponseDictionary:" + dicName + " forKey:@\"" + keyName + "\" acceptNil:"
        if allowNull :
            resultString += "YES"
        else :
            resultString += "NO"

        resultString += " error:error];\n"
        resultString += self.getHandleErrorCode("*error", "", returnVarName, indentDepth)
        return resultString

    def getGetterFromArrayCode(self, className, varName, arrayName, indexVar, allowNull, indentDepth, returnVarName) :
        resultString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth+1)        
        resultString += firstIndent + className + varName + " = [" + self.projectPrefix + "APIParser objectFromResponseArray:" + arrayName + " atIndex:" + indexVar
        resultString += " acceptNil:"
        if allowNull :
            resultString += "YES"
        else :
            resultString += "NO"
        resultString += " error:error];\n"
        resultString += self.getHandleErrorCode("*error", "", returnVarName, indentDepth)
        return resultString
    
    def propertyDefinitionString(self, schemeObj) :
        resultString = ""
        
        if schemeObj.isNaturalType() :
            if schemeObj.rootBaseType() == "boolean" :
                return "@property (nonatomic, assign) BOOL " + self.makeVarName(schemeObj) + ";\n"
            elif schemeObj.rootBaseType() == "string" :
                return "@property (nonatomic, strong) NSString *" + self.makeVarName(schemeObj) + ";\n"
            elif schemeObj.rootBaseType() == "date" :
                return "@property (nonatomic, strong) NSDate *" + self.makeVarName(schemeObj) + ";\n"
            elif schemeObj.rootBaseType() == "data" :
                return "@property (nonatomic, strong) NSData *" + self.makeVarName(schemeObj) + ";\n"
            elif schemeObj.rootBaseType() == "number" :
                return "@property (nonatomic, strong) NSNumber *" + self.makeVarName(schemeObj) + ";\n"
            elif schemeObj.rootBaseType() == "array" :
                return "@property (nonatomic, strong) NSArray *" + self.makeVarName(schemeObj) + ";\n"
            else :
                return "@property (nonatomic, strong) id " + self.makeVarName(schemeObj) + ";\n"

        elif schemeObj.rootBaseType() == "multi" or schemeObj.rootBaseType() == "any" :
            return "@property (nonatomic, strong) NSDictionary *" + self.makeVarName(schemeObj) + ";\n"
        
        
        return "@property (nonatomic, strong) "+ schemeObj.getClassName() +" *" + self.makeVarName(schemeObj) + ";\n"

    def propertyDecodeString(self, schemeObj, indentDepth) :
        firstIndent = self.getIndentString(indentDepth)
        if schemeObj.isNaturalType() and schemeObj.rootBaseType() == "boolean" :
            return firstIndent +  "self." + self.makeVarName(schemeObj) + " = [coder decodeBoolForKey:@\"" + schemeObj.type_name + "\"];\n"

        return firstIndent + "self." + self.makeVarName(schemeObj) + " = [coder decodeObjectForKey:@\"" + schemeObj.type_name + "\"];\n"

    def propertyEncodeString(self, schemeObj, indentDepth) :
        firstIndent = self.getIndentString(indentDepth)
        if schemeObj.isNaturalType() and schemeObj.rootBaseType() == "boolean" :
            return firstIndent + "[coder encodeBool:self." + self.makeVarName(schemeObj)+ " forKey:@\"" + schemeObj.type_name+"\"];\n"

        return firstIndent + "[coder encodeObject:self." + self.makeVarName(schemeObj)+ " forKey:@\"" + schemeObj.type_name+"\"];\n"

    def setPropertyDictionaryString(self, schemeObj, dicName, indentDepth) :
        returnString = ""
        firstIndent = self.getIndentString(indentDepth)
        secondIndent = self.getIndentString(indentDepth + 1)
        thirdIndent = self.getIndentString(indentDepth + 2)
        returnString += firstIndent + "if (self." + self.makeVarName(schemeObj) + ") {\n"
        if schemeObj.isNaturalType() :
            if schemeObj.rootBaseType() == "boolean" :
                returnString += secondIndent + "[" + dicName+ " setObject:[NSNumber numberWithBool:self." + self.makeVarName(schemeObj) + "] forKey:@\"" + schemeObj.type_name + "\"];\n"
            elif schemeObj.rootBaseType() == "date" :
                dateObjSubType = schemeObj.getSubType()
                if len(dateObjSubType) and dateObjSubType[0] == str("ms") :
                    returnString += secondIndent + "NSNumber* number = @([self." + self.makeVarName(schemeObj) + " timeIntervalSince1970] * 1000);\n"
                    returnString += secondIndent + "NSNumberFormatter *formatter = [[NSNumberFormatter alloc] init];\n"
                    returnString += secondIndent + "[formatter setNumberStyle:NSNumberFormatterNoStyle];\n"
                    returnString += secondIndent + "[formatter setNegativeFormat:@\"0\"];\n"
                    returnString += secondIndent + "NSString *value = [formatter stringFromNumber:number];\n"
                    returnString += secondIndent + "NSNumber *convertedNumber = [formatter numberFromString:value];\n"
                    returnString += secondIndent + "[" + dicName+ " setObject:convertedNumber forKey:@\"" + schemeObj.type_name + "\"];\n";
                else :
                    returnString += secondIndent + "[" + dicName+ " setObject:[NSNumber numberWithInteger:[[NSNumber numberWithDouble:[self." + self.makeVarName(schemeObj) + " timeIntervalSince1970]] longValue]] forKey:@\"" + schemeObj.type_name + "\"];\n";
            elif schemeObj.rootBaseType() == "array" :
                arrayObjType = schemeObj.getSubType()
                if arrayObjType and len(arrayObjType) == 1 and schemeObj.hasScheme(arrayObjType[0]) == True :
                    arraySchemeObj = schemeObj.getScheme(arrayObjType[0])
                    returnString += secondIndent + "NSMutableArray *tmpArray = [[NSMutableArray alloc] init];\n"
                    if arraySchemeObj.rootBaseType() == "object" :
                        returnString += secondIndent + "for (" + arraySchemeObj.getClassName() + " *tmpObj in self." + self.makeVarName(schemeObj) + ") {\n"
                        returnString += thirdIndent + "[tmpArray addObject:[tmpObj propertyDictionary]];\n"
                    else :
                        returnString += secondIndent + "for (id tmpObj in self." + self.makeVarName(schemeObj) + ") {\n"
                        returnString += thirdIndent + "[tmpArray addObject:tmpObj];\n"

                    returnString += secondIndent + "}\n"
                    returnString += secondIndent + "[" + dicName + " setObject:tmpArray forKey:@\"" + schemeObj.type_name + "\"];\n"
                else :
                    returnString += secondIndent + "[" + dicName + " setObject:self." + self.makeVarName(schemeObj) + " forKey:@\"" + schemeObj.type_name + "\"];\n"
            else :
                returnString += secondIndent + "[" + dicName + " setObject:self." + self.makeVarName(schemeObj) + " forKey:@\"" + schemeObj.type_name + "\"];\n"
        elif schemeObj.rootBaseType() == "multi" or schemeObj.rootBaseType() == "any" :
                returnString += secondIndent + "[" + dicName + " setObject:self." + self.makeVarName(schemeObj) + " forKey:@\"" + schemeObj.type_name + "\"];\n"
        else :
            returnString += secondIndent + "[" + dicName + " setObject:[self." + self.makeVarName(schemeObj) + " propertyDictionary] forKey:@\"" + schemeObj.type_name + "\"];\n"

        returnString += firstIndent + "}\n"
        return returnString


class TemplateCodeGenerator :
    
    projectPrefix = ""
    dirPath = ""
    templatePath = "./templates"

    def __init__(self):
        projectPrefix = "S2M"
        dirPath = "classes"
        templatePath = "./templates"
    def writeNSStringCategory(self) :
        today = datetime.date.fromtimestamp(time.time())
        if not os.path.exists(self.dirPath):
            os.makedirs(self.dirPath)

        headerDstFile = open(self.dirPath + "/NSString+RegExValidation.h", "w")
        headerSrcFile = self.templatePath + "/NSString+RegExValidation.h"

        try:
            for line in open(headerSrcFile):
                newLine = line.replace('_DATE_', "")
                newLine = newLine.replace('_YEAR_', str(today.year))
                headerDstFile.write(newLine)
        finally :
            headerDstFile.close()

        implDstFile = open(self.dirPath + "/NSString+RegExValidation.m", "w")
        implSrcFile = self.templatePath + "/NSString+RegExValidation.m"

        try:
            for line in open(implSrcFile):
                newLine = line.replace('_DATE_', "")
                newLine = newLine.replace('_YEAR_', str(today.year))
                implDstFile.write(newLine)
        finally :
            implDstFile.close()

    def writeAPIParser(self) :
        today = datetime.date.fromtimestamp(time.time())
        if not os.path.exists(self.dirPath):
            os.makedirs(self.dirPath)

        headerDstFile = open(self.dirPath + "/"+self.projectPrefix+"APIParser.h", "w")
        headerSrcFile = self.templatePath + "/APIParser/APIParser.h"


        try:
            for line in open(headerSrcFile):
                newLine = line.replace('_DATE_', "")
                newLine = newLine.replace('_YEAR_', str(today.year))
                newLine = newLine.replace('_PREFIX_', self.projectPrefix)
                headerDstFile.write(newLine)
        finally :
            headerDstFile.close()

        implDstFile = open(self.dirPath + "/"+self.projectPrefix+"APIParser.m", "w")
        implSrcFile = self.templatePath + "/APIParser/APIParser.m"

        try:
            for line in open(implSrcFile):
                newLine = line.replace('_DATE_', "")
                newLine = newLine.replace('_YEAR_', str(today.year))
                newLine = newLine.replace('_PREFIX_', self.projectPrefix)
                implDstFile.write(newLine)
        finally :
            implDstFile.close()

    def writeTemplates(self) :

        if self.dirPath.endswith("/") :
            self.dirPath = self.dirPath[:-1]
        baseDirPath = self.dirPath
        self.dirPath = baseDirPath + "/Utilities/NSString"
        self.writeNSStringCategory()
        self.dirPath = baseDirPath + "/Utilities/APIParser"
        self.writeAPIParser()


        
    
    























