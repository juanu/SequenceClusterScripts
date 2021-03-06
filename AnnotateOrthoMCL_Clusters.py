#!/usr/local/bin/python
#Created on 3/26/13

__author__ = 'Juan A. Ugalde'

#import sys
from collections import defaultdict
from SummarizeOrthoMCLResults import read_genome_list


def parse_annotation_folder(genome_jgi_list, annotation_folder):
    """
    Takes the folder with annotation files, and parse each annotation
    Returns a dictionary with all the annotation
    """
    genomes_cog_number = {}
    genomes_cog_category = {}
    genomes_product_name = {}
    genomes_pfam_number = {}

    description_cogs = {}
    description_pfams = {}

    for genome in genome_jgi_list:
        #This required the file to have the extension .info.xls
        #This can be changed later
        genome_file = annotation_folder + "/" + genome + ".info.xls"
        cog_number, cog_category, product_name, pfam_number, desc_cog, desc_pfam = parse_jgi_annotation(genome_file)

        genomes_cog_number.update(cog_number)
        genomes_cog_category.update(cog_category)
        genomes_product_name.update(product_name)
        genomes_pfam_number.update(pfam_number)
        description_cogs.update(desc_cog)
        description_pfams.update(desc_pfam)

    return genomes_cog_number, genomes_cog_category, genomes_product_name, genomes_pfam_number, \
           description_cogs, description_pfams


def parse_jgi_annotation(jgi_file):
    """
    Takes a jgi annotation file, and returns dictionaries with the annotations.
    """

    import re

    cog_number = {}
    cog_category = {}
    product_name = {}
    pfam_number = {}

    description_cogs = {}
    description_pfams = {}

    input_file = open(jgi_file, 'r')

    for line in input_file:
        line = line.rstrip('\n')
        if not line.startswith("gene_oid"):

            gene_oid, locus_tag, source, cluster_information, gene_information, evalue = line.split("\t")

            search_cog_number = re.match('(COG\d+)', source)

            if source.startswith("COG_category"):
                cog_category[gene_oid] = cluster_information

            if search_cog_number:
                cog_number[gene_oid] = source
                description_cogs[source] = cluster_information

            if source.startswith("pfam"):
                pfam_number[gene_oid] = source

                description_pfams[source] = cluster_information

            if source.startswith("Product_name"):
                product_name[gene_oid] = gene_information

    return cog_number, cog_category, product_name, pfam_number, description_cogs, description_pfams


def get_cluster_information(input_cluster_file):
    cluster_file = open(input_cluster_file, 'r')

    clusters = {}

    for line in cluster_file:
        line = line.rstrip()

        cluster_id, gene_list = line.split("\t")
        clusters[cluster_id] = gene_list

    return clusters


def annotate_cluster(annotation, clusters):
    """
    This function takes an annotation an the list of clusters and annotates each cluster based on
    the majority rule. The return is a dictionary with the annotation of each cluster, and a dictionary
    with the cluster with conflicts
    """
    annotated_clusters = {}
    total_conflicts = defaultdict(lambda: defaultdict(int))
    unresolved_conflicts = defaultdict(lambda: defaultdict(int))

    for cluster in clusters:
        protein_id_list = [id_tag.split("|")[1] for id_tag in clusters[cluster].split(",")]

        summary_annotation = defaultdict(int)

        for protein_id in protein_id_list:
            if not protein_id in annotation:
                continue
            else:
                protein_info = annotation[protein_id]
                summary_annotation[protein_info] += 1

        if len(summary_annotation) == 0:
            continue

        elif len(summary_annotation) == 1:
            annotated_clusters[cluster] = summary_annotation.keys()[0]

        else:
            total_conflicts[cluster] = summary_annotation
            #Get the total number of values
            total_annotations = sum(summary_annotation.itervalues())
            top_hit = None

            for hit in summary_annotation:
                if summary_annotation[hit] / float(total_annotations) > float(0.5):
                    top_hit = hit

            #Check where no decision was made
            if top_hit is None:
                unresolved_conflicts[cluster] = summary_annotation
            else:
                annotated_clusters[cluster] = top_hit

    return annotated_clusters, total_conflicts, unresolved_conflicts

if __name__ == '__main__':
    import os
    import argparse

    program_description = "This script annotates a cluster generated by the SummarizeOrthoMCLResults script"

    parser = argparse.ArgumentParser(description=program_description)

    #Arguments
    parser.add_argument("-l", "--genome_list_index", type=str,
                        help="File with the genome list. Format GenomeID, FullName, ShortName", required=True)
    parser.add_argument("-a", "--annotation_folder", type=str,
                        help="Folder with the annotation files from JGI", required=True)
    parser.add_argument("-c", "--cluster_file", type=str,
                        help="Cluster file", required=True)
    parser.add_argument("-o", "--output_directory", type=str,
                        help="Output folder", required=True)

    args = parser.parse_args()

    #Create the output directory
    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)

    #####Read the genome list
    genome_id_dictionary, genome_count = read_genome_list(args.genome_list_index)

    ##Read the annotation
    cog_number, cog_category, product_name, pfam_number, description_cogs, description_pfams \
        = parse_annotation_folder(genome_id_dictionary.keys(), args.annotation_folder)

    ##Get the cluster information
    cluster_information = get_cluster_information(args.cluster_file)

    ###Consolidate the annotation for each cluster
    #Cog Number
    cog_number_annotated_clusters, cog_number_total_conflicts, cog_number_unresolved_conflicts\
        = annotate_cluster(cog_number, cluster_information)

    #Cog category
    cog_category_annotated_clusters, cog_category_total_conflicts, cog_category_unresolved_conflicts = \
        annotate_cluster(cog_category, cluster_information)

    #Product name
    product_annotated_clusters, product_total_conflicts, product_unresolved_conflicts = \
        annotate_cluster(product_name, cluster_information)

    #Pfam number
    pfam_annotated_clusters, pfam_total_conflicts, pfam_unresolved_conflicts = \
        annotate_cluster(pfam_number, cluster_information)

    ###Print the outputs
    #Open files
    output_cog_number = open(args.output_directory + "/cog_number_clusters.txt", 'w')
    output_cog_number_conflicts = open(args.output_directory + "/cog_number_conflicts.txt", 'w')
    output_cog_category = open(args.output_directory + "/cog_category_clusters.txt", 'w')
    output_cog_category_conflicts = open(args.output_directory + "/cog_category_conflicts.txt", 'w')
    output_pfam = open(args.output_directory + "/pfam_clusters.txt", 'w')
    output_pfam_conflicts = open(args.output_directory + "/pfam_conflicts.txt", 'w')
    output_product = open(args.output_directory + "/product_name_clusters.txt", 'w')
    output_product_conflicts = open(args.output_directory + "/product_name_conflicts.txt", 'w')

    ##Print log file
    logfile = open(args.output_directory + "/logfile.txt", 'w')

    ##Total number of clusters
    logfile.write("Total number of analyzed clusters: %d" % len(cluster_information) + "\n")

    ##Write output files
    #Cogs
    for cluster in cog_number_annotated_clusters:
        output_cog_number.write(cluster + "\t" + cog_number_annotated_clusters[cluster] + "\t" +
                                description_cogs[cog_number_annotated_clusters[cluster]] + "\n")

    for cluster in cog_number_unresolved_conflicts:
        print_list = []
        for cog in cog_number_total_conflicts[cluster]:
            cog_info = description_cogs[cog]
            print_list.append(cog)
            print_list.append(cog_info)
            print_list.append(str(cog_number_total_conflicts[cluster][cog]))

        output_cog_number_conflicts.write(cluster + "\t" + "\t".join(print_list) + "\n")

    logfile.write("COG Number" + "\n")
    logfile.write("Total annotated cluster: %d" % len(cog_number_annotated_clusters) + "\n")
    logfile.write("Total number of unresolved conflicts: %d" % len(cog_number_unresolved_conflicts) + "\n" + "\n")

    #Cog category
    for cluster in cog_category_annotated_clusters:
        output_cog_category.write(cluster + "\t" + cog_category_annotated_clusters[cluster] + "\n")

    for cluster in cog_category_unresolved_conflicts:
        print_list = []
        for cog_category in cog_category_unresolved_conflicts[cluster]:
            print_list.append(cog_category)
            print_list.append(str(cog_category_unresolved_conflicts[cluster][cog_category]))

        output_cog_category_conflicts.write(cluster + "\t" + "\t".join(print_list) + "\n")

    logfile.write("COG Category" + "\n")
    logfile.write("Total annotated cluster: %d" % len(cog_category_annotated_clusters) + "\n")
    logfile.write("Total number of unresolved conflicts: %d" % len(cog_category_unresolved_conflicts) + "\n" + "\n")

    #Pfam
    for cluster in pfam_annotated_clusters:
        output_pfam.write(cluster + "\t" + pfam_annotated_clusters[cluster] + "\t" +
                          description_pfams[pfam_annotated_clusters[cluster]] + "\n")

    for cluster in pfam_unresolved_conflicts:
        print_list = []
        for pfam in pfam_unresolved_conflicts[cluster]:
            pfam_info = description_pfams[pfam]
            print_list.append(pfam)
            print_list.append(pfam_info)
            print_list.append(str(pfam_unresolved_conflicts[cluster][pfam]))

        output_pfam_conflicts.write(cluster + "\t" + "\t".join(print_list) + "\n")

    logfile.write("Pfam number" + "\n")
    logfile.write("Total annotated cluster: %d" % len(pfam_annotated_clusters) + "\n")
    logfile.write("Total number of unresolved conflicts: %d" % len(pfam_unresolved_conflicts) + "\n" + "\n")

    #Product name
    for cluster in product_annotated_clusters:
        output_product.write(cluster + "\t" + product_annotated_clusters[cluster] + "\n")

    for cluster in product_unresolved_conflicts:
        print_list = []
        for product in product_unresolved_conflicts[cluster]:
            print_list.append(product)
            print_list.append(str(product_unresolved_conflicts[cluster][product]))

        output_product_conflicts.write(cluster + "\t" + "\t".join(print_list) + "\n")

    logfile.write("Product name" + "\n")
    logfile.write("Total annotated cluster: %d" % len(product_annotated_clusters) + "\n")
    logfile.write("Total number of unresolved conflicts: %d" % len(product_unresolved_conflicts) + "\n" + "\n")










    #Close files
    output_cog_number.close()
    output_cog_number_conflicts.close()
    output_cog_category.close()
    output_cog_category_conflicts.close()
    output_pfam.close()
    output_pfam_conflicts.close()
    output_product.close()
    output_product_conflicts.close()
    logfile.close()

    #print len(cog_number_annotated_clusters), len(cog_number_total_conflicts), len(cog_number_unresolved_conflicts)
    #print len(product_annotated_clusters), len(product_conflicts_total_conflicts), len(product_unresolved_conflicts)
    #print len(pfam_annotated_clusters), len(pfam_total_conflicts), len(pfam_unresolved_conflicts)
    #print len(cog_category_annotated_clusters), len(cog_category_total_conflicts), len(cog_category_unresolved_conflicts)
    #print cog_category_unresolved_conflicts

