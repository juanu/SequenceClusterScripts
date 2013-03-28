#!/usr/local/bin/python
#Created on 2/12/13

__author__ = 'Juan Ugalde'

"""This script takes a folder with fasta files (DNA) and a list of the genomes in the following format:
Prefix_Fasta_File\tGenome_Name\tNewID

The idea is to replace the prefix on each fasta file, with the NewID, to be used for the OrthoMCL analysis

"""

def read_genome_list(input_file):

    """
    Function used to read the genome list. The output is a dictionary with the genome list (fasta_prefix -> new_prefix) and the total number of genomes in the list

    """

    genome_count=0
    genome_info={}
    for line in open(input_file,'r'):
        line=line.rstrip()
        element=line.split("\t")
        genome_info[element[0]]=element[2]
        genome_count += 1

    return genome_info,genome_count

def modify_fasta(fasta_file,new_fasta_prefix,output_directory):
    """
    The input is a fasta file. This will rename the file with the new ID, and modify each ID in each entry of the fasta file
    """

    from Bio import SeqIO #Import from tools to read fasta, from Biopython
    genome_output=open(output_directory + "/" + new_fasta_prefix + "." + "fasta","w")

    #Rename the fasta
    for record in SeqIO.parse(fasta_file,"fasta"):
        genome_output.write(">" + new_fasta_prefix + "|" + record.id + "\n")
        genome_output.write(str(record.seq) + "\n")


    genome_output.close()


#For standalone use
if __name__=='__main__':
    import argparse
    import os

    program_description="This script prepares a set of fasta files for running OrthoMCL"
    parser = argparse.ArgumentParser(description=program_description)

    parser.add_argument("-l","--genome_list_index",type=str,help="File with the genome Taxoid, species name and the ID to replace",required=True)
    parser.add_argument("-f","--fasta_directory",type=str,help="Folder with the fasta files (downloaded from JGI)",required=True)
    parser.add_argument("-o","--output_directory",type=str,help="Output folder for the modified fasta files",required=True)

    args=parser.parse_args()

    #Create the output directory
    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)


    #Read the genome list, and create the dictionary

    genome_dictionary,total_genome_count=read_genome_list(args.genome_list_index)

    for genome in genome_dictionary:
        fasta_file=args.fasta_directory + "/" + genome + "." + "fna" #This needs to be more universal
        modify_fasta(fasta_file,genome_dictionary.get(genome),args.output_directory)



    #Print output
    print "A total of %d genomes were renamed" %total_genome_count


















