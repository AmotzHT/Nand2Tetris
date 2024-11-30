# VM translator by amotz the human and Jack the AI
import os
import sys

SEG = {"LOCAL":"LCL", "ARGUMENT":"ARG", "THIS":"THIS", "THAT":"THAT"}
eq_counter = 0
gt_counter = 0
lt_counter = 0
cl_counter = 0
static_filename = ""

def bootstrap():
    bootstrap_command = "@256      // Initialize SP to 256\nD=A\n@SP\nM=D\n@RETURN_BOOTSTRAP   // Push return address\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@LCL            // Push LCL\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@ARG            // Push ARG\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@THIS           // Push THIS\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@THAT           // Push THAT\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@SP             // ARG = SP-5\nD=M\n@5\nD=D-A\n@ARG\nM=D\n@SP             // LCL = SP\nD=M\n@LCL\nM=D\n@SYS.INIT       // Jump to SYS.INIT\n0;JMP\n(RETURN_BOOTSTRAP)\n\n"
    return bootstrap_command

def parser(data):
    parsed_data = [line.split("//")[0].strip() for line in data if line.strip() and not line.strip().startswith("//")]
    return parsed_data

def command_parser(parsed_data):
    translated = []
    for line in parsed_data:
        parm = line.split(" ")
        com, seg, i = (parm[0].upper(), parm[1].upper() if len(parm) > 1 else None, int(parm[2]) if len(parm) > 2 else None) #unpack tuple
        translated.append(translate_command(com, seg, i, line)) # call translation function and append results to translated line list
    return translated

def translate_command(com, seg=None, i=None, line=None):
    global eq_counter, gt_counter, lt_counter, cl_counter, static_filename, SEG

    if com == "PUSH":
        if seg == "CONSTANT":
            trans_command = f"// {line}\n@{i}\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"      

        elif seg in SEG:   # LOCAL, ARGUMENT, THIS, THAT
            trans_command = f"// {line}\n@{i}\nD=A\n@{SEG[seg]}\nA=D+M\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"

        elif seg == "TEMP":
            trans_command = f"// {line}\n@{5 + i}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"     

        elif seg == "POINTER": # Pointer 0 points to THIS; Pointer 1 points to THAT
            pointer = ["THIS", "THAT"]
            trans_command = f"// {line}\n@{pointer[i]}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"

        elif seg == "STATIC":    
            trans_command = f"// {line}\n@{static_filename}.{i}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"

        else:
            # handel unknown segments
            trans_command = f"Unknown segment '{seg}' in line: {line}"
            raise ValueError(trans_command)

    elif com == "POP":
        if seg in SEG:   # LOCAL, ARGUMENT, THIS, THAT
            trans_command = f"// {line}\n@{i}\nD=A\n@{SEG[seg]}\nD=D+M\n@R13\nM=D\n@SP\nAM=M-1\nD=M\n@R13\nA=M\nM=D\n"       

        elif seg == "TEMP":
            trans_command = f"// {line}\n@SP\nAM=M-1\nD=M\n@{5+i}\nM=D\n"   

        elif seg == "POINTER": # Pointer 0 points to THIS; Pointer 1 points to THAT
            pointer = ["THIS", "THAT"]
            trans_command = f"// {line}\n@SP\nAM=M-1\nD=M\n@{pointer[i]}\nM=D\n"

        elif seg == "STATIC":# For static variables, naming convention `filename.i`
            trans_command = f"// {line}\n@SP\nAM=M-1\nD=M\n@{static_filename}.{i}\nM=D\n"

        else:
            # Handle unknown segments
            trans_command = f"Unknown segment '{seg}' in line: {line}"
            raise ValueError(trans_command)
            
    elif com == "ADD":
        trans_command = f"// {line}\n@SP\nAM=M-1\nD=M\nA=A-1\nM=D+M\n"

    elif com == "SUB":
        trans_command = f"// {line}\n@SP\nAM=M-1\nD=M\nA=A-1\nM=M-D\n"

    elif com == "NEG":
        trans_command = f"// {line}\n@SP\nA=M-1\nM=-M\n"

    elif com == "EQ":
        trans_command = f"// {line}\n@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\n@EQUAL.{eq_counter}.true\nD;JEQ\n@SP\nA=M-1\nM=0\n@EQUAL.{eq_counter}.end\n0;JMP\n(EQUAL.{eq_counter}.true)\n@SP\nA=M-1\nM=-1\n(EQUAL.{eq_counter}.end)\n"
        eq_counter += 1

    elif com == "GT":
        trans_command = f"// {line}\n@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\n@GT.{gt_counter}.true\nD;JGT\n@SP\nA=M-1\nM=0\n@GT.{gt_counter}.end\n0;JMP\n(GT.{gt_counter}.true)\n@SP\nA=M-1\nM=-1\n(GT.{gt_counter}.end)\n"
        gt_counter += 1

    elif com == "LT":
        trans_command = f"// {line}\n@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\n@LT.{lt_counter}.true\nD;JLT\n@SP\nA=M-1\nM=0\n@LT.{lt_counter}.end\n0;JMP\n(LT.{lt_counter}.true)\n@SP\nA=M-1\nM=-1\n(LT.{lt_counter}.end)\n"
        lt_counter += 1

    elif com == "AND":
        trans_command = f"// {line}\n@SP\nAM=M-1\nD=M\nA=A-1\nM=M&D\n"

    elif com == "OR":
        trans_command = f"// {line}\n@SP\nAM=M-1\nD=M\nA=A-1\nM=M|D\n"

    elif com == "NOT":
        trans_command = f"// {line}\n@SP\nA=M-1\nM=!M\n"

    elif com == "LABEL": # seg = label
        trans_command = f"// {line}\n({seg})\n"

    elif com == "GOTO": # seg = label
        trans_command = f"// {line}\n@{seg}\n0;JMP\n"

    elif com == "IF-GOTO":  # seg = label
        trans_command = f"// {line}\n@SP\nAM=M-1\nD=M\n@{seg}\nD;JNE\n"

    elif com == "FUNCTION": # seg = function name , i = number of variabls
        trans_command = f"// {line}\n({seg})\n"

        if int(i) > 0:
            for _ in range(int(i)):
                trans_command += "@SP\nA=M\nM=0\n@SP\nM=M+1\n"

    elif com == "CALL": # seg = function name , i = number of variabls
        trans_command = (f"// {line}\n@RETURN_{seg}.{cl_counter}   // Push return address\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@LCL                         // save LCL\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@ARG                         // save ARG\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@THIS                        // save THIS\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@THAT                        // save THAT\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@SP                          // Reposition ARG = SP-5-{i}\nD=M\n@5\nD=D-A\n@{i}\nD=D-A\n@ARG\nM=D\n@SP                          // set LCL = SP\nD=M\n@LCL\nM=D\n@{seg}                       // Jump to function\n0;JMP\n(RETURN_{seg}.{cl_counter})  // Return label\n")
        cl_counter += 1

    elif com == "RETURN":
        trans_command = (f"// {line}\n@LCL                      // Save LCL in R13 (Frame)\nD=M\n@R13\nM=D\n@5                        // Save return address (R14) using Frame-5\nA=D-A\nD=M\n@R14\nM=D\n@SP                       // Reposition the return value for the caller\nM=M-1\nA=M\nD=M\n@ARG\nA=M\nM=D\n@ARG                      // Restore SP = ARG + 1\nD=M+1\n@SP\nM=D\n@R13                      // Restore THAT = *(Frame - 1)\nD=M\n@1\nA=D-A\nD=M\n@THAT\nM=D\n@R13                      // Restore THIS = *(Frame - 2)\nD=M\n@2\nA=D-A\nD=M\n@THIS\nM=D\n@R13                      // Restore ARG = *(Frame - 3)\nD=M\n@3\nA=D-A\nD=M\n@ARG\nM=D\n@R13                      // Restore LCL = *(Frame - 4)\nD=M\n@4\nA=D-A\nD=M\n@LCL\nM=D\n@R14                      // Jump to return address (R14)\nA=M\n0;JMP\n")

    else:                # Handle unknown command
        trans_command = f"Unknown command '{com}' in line: {line}"
        raise ValueError(trans_command)
    
    return trans_command

def print_help():
    print("""
Usage: python VM_translator.py [input_path]

Arguments:
  input_path    The path to a .vm file or a directory containing .vm files.
                If the path contains spaces, make sure to wrap it in quotes.

Examples:
  python VM_translator.py "C:\\path with spaces\\filname.vm"
  python VM_translator.py "C:\\path with spaces\\directory"

Options:
  --help        Show this help message and exit.
    """)

def check_path(input_path):
    if '--help' in sys.argv or '-h' in sys.argv:
        print_help()
        sys.exit(0)
   
    if len(sys.argv) > 2 and not os.path.isdir(input_path) and not os.path.isfile(input_path): # error reaulting from spaces in file/dir name
        print(f"****\nWarning: If your input path contains spaces, make sure to wrap it in quotes.\nExample: python VM_translator.py \"{' '.join(sys.argv[1:])}\"\n****")
        sys.exit(0)
    

def main():
    global static_filename
    
    input_path = sys.argv[1] if len(sys.argv) > 1 else "projects 2024\\8\\FunctionCalls\\FibonacciElement"  
    input_path = os.path.abspath(input_path)   # Get absolute path 
    check_path(input_path)


    if os.path.isdir(input_path):
        dir_name = os.path.basename(input_path)
        output_file = os.path.join(input_path, f"{dir_name}.asm")
        
        all_translated = [bootstrap(),]
        files = sorted(os.listdir(input_path), key=lambda x: (x != "Sys.vm", x)) # sorting by tupple (created by lambda for each file) consists of boolean and file name

        for filename in files:
            if filename.endswith('.vm'):
                input_file = os.path.join(input_path, filename)
                with open(input_file, "r") as file_object:
                    data = file_object.readlines()
                parsed_data = parser(data)
                static_filename = filename[:-3].upper()
                translated = command_parser(parsed_data)
                all_translated.extend(translated)
        
        with open(output_file, "w") as save_file_object:
            save_file_object.write("\n".join(all_translated))
            print(f"file created successfuly at: {output_file}")
            
    else:  
        if not input_path.endswith('.vm'):
            print("Error: Single file input must be a .vm file")
            return
            
        output_file = input_path.replace('.vm', '.asm')
        with open(input_path, "r") as file_object:
            data = file_object.readlines()
        parsed_data = parser(data)
        translated = command_parser(parsed_data)
        with open(output_file, "w") as save_file_object:
            save_file_object.write("\n".join(translated))
            print(f"file created successfuly at: {output_file}")

if __name__ == "__main__":
    main()