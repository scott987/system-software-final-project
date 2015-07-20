import sys
import math

lineCount = 0


def codeSplit(line, nPass):
    line = line.replace("\n", "")
    line = line.split('\t')
    if nPass == 1 and line[0] != '.' and line[1] == '':
        del line[1]
    return line


def readLine(file, nPass=1):
    global lineCount
    lineCount = lineCount + 1
    return codeSplit(file.readline(), nPass)


def writeLine(file, loc, line):
    if line[0] != '.' and line[1] != "END":
        file.write("%X" % loc)
    for str in line:
        file.write("\t" + str)
    file.write("\n")

# OPTAB format = [object code,format x]
OPTAB = {}
for l in open("OPTAB", 'r'):
    l = l.replace("\n", "")
    l = l.split(' ')
    OPTAB[l[0]] = [int(l[1], 16), int(l[2])]

SYMTAB = {}

REGISTER = {
    'A': 0, 'X': 1,
    'L': 2, 'B': 3,
    'S': 4, 'T': 5,
    'F': 6, 'PC': 8,
    'SW': 9,
}

B = 0


def ObjectCode(operand, formatfour=False):
    ob = 0
    if operand[0] == "":
        ob |= (int('110000', 2) << 12)
    elif operand[0][0] == '#':  # immeiadte
        if not formatfour:
            if operand[0][1:].isdigit():
                ob |= (int('010000', 2) << 12)
                ob |= int(operand[0][1:])
            elif operand[0][1:] in SYMTAB:
                target = SYMTAB[operand[0][1:]] - (int(line[0], 16) + 3)
                if target >= -2048 and target <= 2047:
                    ob |= (int('010010', 2) << 12)
                    if target < 0:
                        ob |= 4096 - (target * -1)
                    else:
                        ob |= target
                elif (B + 4095) >= SYMTAB[operand[0][1:]]:
                    ob |= (int('010100', 2) << 12)
                    ob |= SYMTAB[operand[0][1:]] - B
                elif SYMTAB[operand[0][1:]] <= int("FFF", 16):
                    ob |= (int('010000', 2) << 12)
                    ob |= SYMTAB[operand[0][1:]]
                else:
                    sys.exit(
                        "At %d,symbol out of range" % lineCount - 1
                    )
            else:
                sys.exit(
                    "At %d,symbol not found" % lineCount - 1
                )
        else:
            ob |= (int('010001', 2) << 20)
            if operand[0][1:].isdigit():
                ob |= int(operand[0][1:])
            elif operand[0][1:] in SYMTAB:
                ob |= SYMTAB[operand[0][1:]]
            else:
                sys.exit(
                    "At %d,symbol not found" % lineCount - 1
                )
    # end if immediate
    elif operand[0][0] == '@':  # indirect
        if not formatfour:
            if operand[0][1:] in SYMTAB:
                target = SYMTAB[operand[0][1:]] - (int(line[0], 16) + 3)
                if target >= -2048 and target <= 2047:
                    ob |= (int('100010', 2) << 12)
                    if target < 0:
                        ob |= 4096 - (target * -1)
                    else:
                        ob |= target
                elif (B + 4095) >= SYMTAB[operand[0][1:]]:
                    ob |= (int('100100', 2) << 12)
                    ob |= SYMTAB[operand[0][1:]] - B
                elif SYMTAB[operand[0][1:]] <= int("FFF", 16):
                    ob |= (int('100000', 2) << 12)
                    ob |= SYMTAB[operand[0][1:]]
                else:
                    sys.exit(
                        "At %d,symbol out of range" % lineCount - 1
                    )
            else:
                sys.exit(
                    "At %d,symbol not found" % lineCount - 1
                )
        else:
            ob |= (int('100001', 2) << 20)
            if operand[0][1:] in SYMTAB:
                ob |= SYMTAB[operand[0][1:]]
            else:
                sys.exit(
                    "At %d,symbol not found" % lineCount - 1
                )
    # end if indirect
    else:
        if not formatfour:
            if operand[0] in SYMTAB:
                target = SYMTAB[operand[0]] - (int(line[0], 16) + 3)
                if target >= -2048 and target <= 2047:
                    ob |= (int('110010', 2) << 12)
                    if target < 0:
                        ob |= 4096 - (target * -1)
                    else:
                        ob |= target
                elif (B + 4095) >= SYMTAB[operand[0]]:
                    ob |= (int('110100', 2) << 12)
                    ob |= SYMTAB[operand[0]] - B
                elif SYMTAB[operand[0]] <= int("FFF", 16):
                    ob |= (int('110000', 2) << 12)
                    ob |= SYMTAB[operand[0]]
                else:
                    sys.exit(
                        "At %d,symbol out of range" % lineCount
                    )
            else:
                sys.exit(
                    "At %d,symbol not found" % lineCount
                )
        else:
            ob |= (int('110001', 2) << 20)
            if operand[0] in SYMTAB:
                ob |= SYMTAB[operand[0]]
            else:
                sys.exit(
                    "At %d,symbol not found" % lineCount
                )
    return ob

# pass 1
loc = 0
start = 0
sourcefile = open(sys.argv[1], 'r')
intermediate = open(sys.argv[1] + ".tem", 'w')

line = readLine(sourcefile)

# if start
if line[1] == "START":
    start = int(line[2])
    loc += start
    lineCount = 0
    SYMTAB[line[0]] = loc
    writeLine(intermediate, loc, line)
    line = readLine(sourcefile)


while line[0] == '.' or line[1] != "END":
    tempLoc = loc
    # if is not comment line
    if line[0] != '.':
        # if there is a label
        if line[0] != '':
            if line[0] in SYMTAB:
                sys.exit(
                    "Compile error!\nAt {0},duplicate symbol({1})".format(
                        lineCount - 1, line[0]
                    )
                )
            else:
                SYMTAB[line[0]] = loc

        format4 = False
        opcode = line[1]
        if line[1][0] == '+':
            format4 = True
            opcode = line[1][1:]
        if opcode in OPTAB:
            if format4:
                loc += 4
            else:
                loc += OPTAB[opcode][1]
        elif opcode == "RESW":
            loc += 3 * int(line[2])
        elif opcode == "RESB":
            loc += int(line[2])
        elif opcode == "BYTE":
            if line[2][0] == 'C':
                loc += len(line[2]) - 3
            elif line[2][0] == 'X':
                loc += math.ceil(len(line[2][2:-2]) / 2)
        elif opcode == "BASE":
            pass
        else:
            sys.exit(
                "Compile error!At {0},invalid operation code({1})".format(
                    lineCount - 1, line[1]
                )
            )
    writeLine(intermediate, tempLoc, line)
    line = readLine(sourcefile)
# while line[1] != end
writeLine(intermediate, loc, line)
sourcefile.close()
intermediate.close()

programLen = loc - start
# end pass 1

symtabOutput = open(sys.argv[1] + ".sym", 'w')
symtabOutput.write("origin:\n{\n")
for symbol in SYMTAB:
    symtabOutput.write("\t" + symbol + ":" + str(SYMTAB[symbol]) + "\n")
symtabOutput.write("}")
symtabOutput.write("hex:\n{\n")
for symbol in SYMTAB:
    symtabOutput.write(
        "\t" + symbol + ":" + hex(SYMTAB[symbol])[2:].upper() + "\n")
symtabOutput.write("}")
symtabOutput.close()


lineCount = 0

# pass 2
intermediate = open(sys.argv[1] + ".tem", 'r')
objectProgam = open(sys.argv[1][:sys.argv[1].find(".")] + ".o", 'w')
modify = []
line = readLine(intermediate)

# header record
hRecord = "H"
start = "000000"

# if start
if line[2] == "START":
    hRecord += line[1].ljust(6, ' ') + line[3].zfill(6).upper()
    start = line[3].zfill(6).upper()
    line = readLine(intermediate, 2)
else:
    hRecord += "      000000"

hRecord += hex(programLen)[2:].upper().zfill(6)
objectProgam.write(hRecord + "\n")
# end header record

# text record
tRecord = "T"
first = 0
setFirst = False
obCode = ""
loc = int(start, 16)
nformat = 0
while line[1] == '.' or line[2] != "END":

    # if not command line
    if line[1] != '.':
        ob = 0
        operand = [""]

        if len(line) >= 4:
            operand = line[3].replace(' ', '').split(',')

        if line[2] in OPTAB:
            loc += OPTAB[line[2]][1]
            ob = OPTAB[line[2]][0]
            nformat = OPTAB[line[2]][1]
            if nformat == 2:
                ob |= (REGISTER[operand[0]] << 4)
                if len(operand) == 2:
                    ob |= REGISTER[operand[0]]
            else:
                ob |= ObjectCode(operand)
        elif line[2][0] == '+':
            nformat = 4
            loc += 4
            ob = OPTAB[line[2][1:]][0] << 8
            ob |= ObjectCode(operand, True)
            if operand[0][0] != '#' and operand[0][0] != '@':
                mRecord = "M" + \
                    hex(int(line[0], 16) + 1)[2:].upper().zfill(6) + "05"
                modify.append(mRecord)
        elif line[2] == "RESW":
            loc += 3 * int(line[3])
        elif line[2] == "RESB":
            loc += int(line[3])
        elif line[2] == 'BYTE':
            if line[3][0] == 'C':
                loc += len(line[3]) - 3
                nformat = len(line[3]) - 3
                locCount = 0
                for c in line[3][2:-1]:
                    ob = (ob << 8) | ord(c)
            elif line[3][0] == 'X':
                nformat = math.ceil(len(line[3][2:-2]) / 2)
                loc += math.ceil(len(line[3][2:-2]) / 2)
                ob |= int(line[3][2:-1], 16)
        elif line[2] == "BASE":
            if operand[0] == '#':
                B = int(operand[0][1:])
            elif operand[0] in SYMTAB:
                B = SYMTAB[operand[0]]
            line = readLine(intermediate, 2)
            continue

        if first == 0 and ob != 0 and obCode == "":
            tRecord += line[0].zfill(6)
            first = int(line[0], 16)
            setFirst = True
        if ob == 0 and obCode != "" and setFirst:
            tRecord += hex(loc - first - nformat)[2:].upper().zfill(2)
            tRecord += obCode + "\nT"
            first = 0
            obCode = ""
            ob = 0
        else:
            if line[2] == 'BYTE':
                obCode += hex(ob)[2:].upper()
            elif ob != 0:
                obCode += hex(ob)[2:].upper().zfill(6)

    # end if not command line

    line = readLine(intermediate, 2)
tRecord += hex(loc - first)[2:].upper().zfill(2) + obCode
# end text record
intermediate.close()

objectProgam.write(tRecord + "\n")

# m record
for m in modify:
    objectProgam.write(m + "\n")

# e record
objectProgam.write("E" + start)

objectProgam.close()
# end pass 2
