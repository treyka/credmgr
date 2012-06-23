#!/usr/bin/env python

import yaml
from sqlite3 import connect, Row
from time import sleep
from subprocess import Popen, PIPE
from re import match, sub
import datetime 
from argparse import ArgumentParser
import passlib.hash

config = {}

def parse_yaml(yaml_file):
    try:
        config = yaml.load(file(yaml_file, 'r'))
    except yaml.YAMLError, exc:
        print("error parsing yaml file: %s; check your syntax!" % (yaml_file))
        exit()
    return config

def shell_exec(cmd):
    p = Popen(cmd, shell=True, stdout=PIPE)
    # wait for subprocess to terminate
    while 1:
        if p.poll() != None:
            output = p.stdout.read()
            result_code = p.poll()
            break
        else:
            sleep(0.1)
    return output, result_code

def gpg_encrypt_message_body(message, gpg_pubkey):
    shell_pipeline_command = """echo -n "%s" | gpg --encrypt --recipient %s --trust-model always -q""" % (message, gpg_pubkey)
    encrypted_message, result_code = shell_exec(shell_pipeline_command)
    return encrypted_message

def make_shard_holder_contact_list(shard_holder, shard_holders_dict):
    shard_holder_contact_list = ""
    for other_shard_holder in shard_holders_dict.keys():
        if other_shard_holder == shard_holder:
            pass
        else:
            contact_dict = shard_holders_dict[other_shard_holder]
            shard_holder_contact_list += """name: %s
primary email: %s
failsafe email: %s
primary phone: %s
failsafe phone: %s
gpg public key id: %s

""" % (contact_dict['name'], contact_dict['primary_email'], \
           contact_dict['failsafe_email'], contact_dict['primary_phone'], \
           contact_dict['failsafe_phone'], contact_dict['gpg_pubkey'])
    return shard_holder_contact_list

def make_email_text(affiliation, shard, shard_holder_dict, shard_holder_contact_list):
    email_body="""Hi, %s -
    You are receiving this email as part of an automated %s process for 
    managing root passwords and other credentials.

%s

""" % (shard_holder_dict['name'], affiliation, shard_holder_contact_list)
    return email_body


def hash_pass(cleartext_pass, hash_type):
    try:
        hash_function = getattr(passlib.hash, hash_type)
        hash = hash_function.encrypt(cleartext_pass)
    except:
        print("problem generating hash_type %s - exiting" % (hash_type))
        exit()
    return hash

def gen_root_pass(pass_length):
    cleartext_pass, result_code = \
        shell_exec("pwgen --secure %i" % (pass_length))
    return cleartext_pass.strip()

def shard_root_pass(cleartext_pass, shard_prefix, \
                        minimum_reassembly_shards, number_of_shards):
    shell_pipeline_command = "echo -n %s | ssss-split -w %s -t %i -n %i -q 2>/dev/null" \
        % (cleartext_pass, shard_prefix, \
               minimum_reassembly_shards, number_of_shards)
    password_chunks, result_code = shell_exec(shell_pipeline_command)
    return password_chunks.splitlines()

def parse_args():
    arg_p = ArgumentParser(description="rootmgr: manage root access using shamir secret sharing")
    arg_p.add_argument('--yaml', help="yaml configuration file", \
                           dest='yaml_file', required=True)
    return vars(arg_p.parse_args())

def main():
    args = parse_args()
    yaml_file = args['yaml_file']
    config = parse_yaml(yaml_file)
    info_dict = config[0]['info']
    shard_holders_list = config[1]['shard_holders']
    shard_prefix = sub('\s', '_', info_dict['credential_name'])
    cleartext_pass = gen_root_pass(info_dict['password_length'])
    hash_types = info_dict['hash_types']
    for hash_type in hash_types:
        crypt_hash = hash_pass(cleartext_pass, hash_type)
        print("%s: %s" % ( hash_type, crypt_hash))
    exit()
    shard_holders_dict = {}
    for i in shard_holders_list:
        # if someone doesn't have a gpg keypair, skip 'em
        if i[i.keys()[0]]['gpg_pubkey'] is None:
            print("%s has no gpg pubkey configured - skipping..." % (i[i.keys()[0]]['name']))
            pass
        else:
            # this is a little fuggly but i'm not going to spend the rest of my life on this
            shard_holders_dict[i.keys()[0]] = i[i.keys()[0]]

    number_of_shards = len(shard_holders_dict.keys())
    # print number_of_shards            
    shards_list = shard_root_pass(cleartext_pass, shard_prefix, \
                                      info_dict['minimum_reassembly_shards'], \
                                      number_of_shards)

    for shard_tuple in enumerate(shard_holders_dict.keys()):
        shard_index = shard_tuple[0]
        shard_holder = shard_tuple[1]
        shard_holder_contact_list = make_shard_holder_contact_list(shard_holder, shard_holders_dict)
        email_body = make_email_text(info_dict['affiliation'], shards_list[shard_index], shard_holders_dict[shard_holder], shard_holder_contact_list)
        encrypted_message_body = gpg_encrypt_message_body(email_body, shard_holders_dict[shard_holder]['gpg_pubkey'])
        print encrypted_message_body


main()
