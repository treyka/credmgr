#!/usr/bin/env python

# Copyright (C) 2012 Trey Darley
# 
# Trey Darley can be contacted at: trey@kingfisherops.com
# 
# Licensed under the Apache License, Version 2.0
#
# Please refer to the included LICENSE file for further details.
#

import yaml
from time import sleep
from subprocess import Popen, PIPE
from re import match, sub
import datetime 
from argparse import ArgumentParser
import passlib.hash
from pwgen import pwgen
from os.path import join
from smtplib import SMTP

timestamp = datetime.datetime.now()
human_friendly_timestamp = timestamp.strftime("%d.%m.%Y %H:%M:%S")

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
    shell_pipeline_command = """echo -n "%s" | gpg --encrypt --recipient %s --trust-model always -q --armor""" % (message, gpg_pubkey)
    encrypted_message, result_code = shell_exec(shell_pipeline_command)
    return encrypted_message

def send_email(defaults, contact,human_friendly_timestamp, message):
    debuglevel = 0
    smtp = SMTP()
    smtp.set_debuglevel(debuglevel)
    smtp.connect('localhost', 25)
    # smtp.login('USERNAME@DOMAIN', 'PASSWORD')

    from_addr = defaults['smtp_from']
    to_addr = "%s <%s>" % (contact['name'], contact['primary_email'])
    if contact['failsafe_email']:
        to_addr += ", %s <%s>" % (contact['name'], contact['failsafe_email'])

    message = """From: %s
Organization: %s
Subject: credmgr password shard: %s 
Date: %s
To: %s
MIME-Version: 1.0
Content-Type: "text/plain; charset=us-ascii"

%s
""" % ( from_addr, defaults['affiliation'], defaults['comment'], human_friendly_timestamp, to_addr, message )

    smtp.sendmail(from_addr, to_addr, message)
    smtp.quit()


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

def make_email_text(defaults_dict, shard, number_of_shards, shard_holder_dict, shard_holder_contact_list, cred_dict,):
    email_body="""Hi, %s -

You are receiving this email as part of a %s automated process for 
managing root passwords and other credentials. 

Keep this email archived someplace safe. 
Make absolutely sure you know where it is.

If you ever need it, probably something has gone horribly wrong.
You may be under tremendous stress.

Make backups!!!

Here is your shard:

%s

You now hold 1/%i existing recovery shards for:
    credential name: %s
    credential comment: %s

A minimum of %i other shards must be joined to your shard to reassemble %s.

Here are the contact details for the people holding the other shards:

%s

""" % (shard_holder_dict['name'], defaults_dict['affiliation'], shard, number_of_shards, cred_dict['name'], cred_dict['comment'], (cred_dict['minimum_reassembly_shards'] -1), cred_dict['name'], shard_holder_contact_list)
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
    cleartext_pass = pwgen(pass_length, no_symbols=True)
    return cleartext_pass

def shard_root_pass(cleartext_pass, shard_prefix, minimum_reassembly_shards, number_of_shards):
    shell_pipeline_command = "echo -n %s | ssss-split -w %s -t %i -n %i -q 2>/dev/null" \
        % (cleartext_pass, shard_prefix, \
               minimum_reassembly_shards, number_of_shards)
    password_chunks, result_code = shell_exec(shell_pipeline_command)
    return password_chunks.splitlines()



def parse_args():
    arg_p = ArgumentParser(description="credmgr: securely manage privileged account credentials via shamir secret sharing")
    arg_p.add_argument('--configdir', help="path to credmgr config files", \
                           dest='config_dir')
    arg_p.add_argument('--cred-yaml', help="path to credential-specific yaml", \
                           dest='cred_yaml', required=True)
    return vars(arg_p.parse_args())

def main():
    args = parse_args()
    cred_yaml = args['cred_yaml']
    config_dir = args['config_dir']
    if config_dir is None:
        config_dir = "./config"
    contacts_yaml = join(config_dir, 'contacts.yaml')
    # the idea is that you can set values in defaults.yaml but override these in cred.yaml
    defaults_yaml = join(config_dir, 'defaults.yaml')
    raw_contacts_dict = parse_yaml(contacts_yaml)[0]['contacts']
    contacts_dict = {}
    # TODO: this is totally fuggly
    for i in raw_contacts_dict:
        contacts_dict[i.keys()[0]] = i[i.keys()[0]]
    defaults_dict = parse_yaml(defaults_yaml)[0]['defaults']
    cred_dict = parse_yaml(cred_yaml)[0]['cred']
    # let's be nice with our filenames and shards
    shard_prefix = sub('\s', '_', cred_dict['name'])
    # generate password
    cleartext_pass = gen_root_pass(cred_dict['password_length'])
    # merge all values defined in cred.yaml into the system defaults...kinda lazy but it does the job
    for key in cred_dict.keys():
        defaults_dict[key] = cred_dict[key]
    if defaults_dict.has_key('hash_types'):
        hash_types = defaults_dict['hash_types']
    else:
        # set a sane default value
        hash_types = ['sha512_crypt', 'bcrypt',]
    for hash_type in hash_types:
        crypt_hash = hash_pass(cleartext_pass, hash_type)
        print("%s: %s" % ( hash_type, crypt_hash))
    shard_holders_list = defaults_dict['shard_holders']
    shard_holders_dict = {}
    for shard_holder in shard_holders_list:
        # make sure all the shard holder contacts are defined
        if shard_holder not in contacts_dict.keys():
            print("%s listed as a shard holder in %s but they are not defined in %s...aborting" % (shard_holder, cred_yaml, contacts_yaml))
            exit()
        # if someone doesn't have a gpg keypair, skip 'em
        elif contacts_dict[shard_holder]['gpg_pubkey'] is None:
            print("%s listed as a shard holder in %s but they have no pubkey defined in %s...aborting" % (shard_holder, cred_yaml, contacts_yaml))
            exit()
        else:
            shard_holders_dict[shard_holder] = contacts_dict[shard_holder]
    number_of_shards = len(shard_holders_list)
    if number_of_shards <= defaults_dict['minimum_reassembly_shards']:
        print("required_shards is set to %i but there are only %i shard holders listed in %s...this makes no sense, check your config...aborting" % (defaults_dict['minimum_reassembly_shards'], number_of_shards, cred_yaml))
    shards_list = shard_root_pass(cleartext_pass, shard_prefix, \
                                  defaults_dict['minimum_reassembly_shards'], \
                                      number_of_shards)
    for shard_tuple in enumerate(shard_holders_dict.keys()):
        shard_index = shard_tuple[0]
        shard_holder = shard_tuple[1]
        shard_holder_contact_list = make_shard_holder_contact_list(shard_holder, shard_holders_dict)
        email_body = make_email_text(defaults_dict, shards_list[shard_index], number_of_shards, shard_holders_dict[shard_holder], shard_holder_contact_list, cred_dict,)
        encrypted_message_body = gpg_encrypt_message_body(email_body, shard_holders_dict[shard_holder]['gpg_pubkey'])
        send_email(defaults_dict, shard_holders_dict[shard_holder], human_friendly_timestamp, encrypted_message_body,)
main()
