"""
AWS-specific checks. Part of the cloud_enum package available at
github.com/initstring/cloud_enum
"""
import asyncio

from enum_tools import utils

BANNER = '''
++++++++++++++++++++++++++
      amazon checks
++++++++++++++++++++++++++
'''

# Known S3 domain names
S3_URL = 's3.amazonaws.com'
APPS_URL = 'awsapps.com'

# Known AWS region names. This global will be used unless the user passes
# in a specific region name. (NOT YET IMPLEMENTED)
AWS_REGIONS = ['amazonaws.com',
               'ap-east-1.amazonaws.com',
               'us-east-2.amazonaws.com',
               'us-west-1.amazonaws.com',
               'us-west-2.amazonaws.com',
               'ap-south-1.amazonaws.com',
               'ap-northeast-1.amazonaws.com',
               'ap-northeast-2.amazonaws.com',
               'ap-northeast-3.amazonaws.com',
               'ap-southeast-1.amazonaws.com',
               'ap-southeast-2.amazonaws.com',
               'ca-central-1.amazonaws.com',
               'cn-north-1.amazonaws.com.cn',
               'cn-northwest-1.amazonaws.com.cn',
               'eu-central-1.amazonaws.com',
               'eu-west-1.amazonaws.com',
               'eu-west-2.amazonaws.com',
               'eu-west-3.amazonaws.com',
               'eu-north-1.amazonaws.com',
               'sa-east-1.amazonaws.com']

def print_s3_response(reply):
    """
    Parses the HTTP reply of a brute-force attempt

    This function is passed into the class object so we can view results
    in real-time.
    """
    if reply.status_code == 404:
        pass
    elif 'Bad Request' in reply.reason:
        pass
    elif reply.status_code == 200:
        utils.printc("    OPEN S3 BUCKET: {}\n"
                     .format(reply.url), 'green')
        utils.list_bucket_contents(reply.url)
    elif reply.status_code == 403:
        utils.printc("    Protected S3 Bucket: {}\n"
                     .format(reply.url), 'orange')
    elif 'Slow Down' in reply.reason:
        print("[!] You've been rate limited, skipping rest of check...")
        return 'breakout'
    else:
        print("    Unknown status codes being received from {}:\n"
              "       {}: {}"
              .format(reply.url, reply.status_code, reply.reason))

def check_s3_buckets(names, threads):
    """
    Checks for open and restricted Amazon S3 buckets
    """
    print("[+] Checking for S3 buckets")

    # Start a counter to report on elapsed time
    start_time = utils.start_timer()

    # Initialize the list of correctly formatted urls
    candidates = []

    # Take each mutated keyword craft a url with the correct format
    for name in names:
        candidates.append('{}.{}'.format(name, S3_URL))

    # Send the valid names to the batch HTTP processor
    utils.get_url_batch(candidates, use_ssl=False,
                        callback=print_s3_response,
                        threads=threads)

    # Stop the time
    utils.stop_timer(start_time)

def check_awsapps(names, threads, nameserver):
    """
    Checks for existence of AWS Apps
    (ie. WorkDocs, WorkMail, Connect, etc.)
    """
    print("[+] Checking for AWS Apps")

    # Start a counter to report on elapsed time
    start_time = utils.start_timer()

    # Initialize the list of domain names to look up
    candidates = []

    # Initialize the list of valid hostnames
    valid_names = []

    # Take each mutated keyword craft a domain name to lookup.
    for name in names:
        candidates.append('{}.{}'.format(name, APPS_URL))

    # AWS Apps use DNS sub-domains. First, see which are valid.
    valid_names = utils.fast_dns_lookup(candidates, nameserver,
                                        threads=threads)

    for name in valid_names:
        utils.printc("    App Found: https://{}\n" .format(name), 'orange')

    # Stop the timer
    utils.stop_timer(start_time)

async def run_all(names, args, pool):
    """
    Function is called by main program
    """
    print(BANNER)
    tasks = []
    loop = asyncio.get_event_loop()
    # Use user-supplied AWS region if provided
    #if not regions:
    #    regions = AWS_REGIONS
    # check_s3_buckets(names, args.threads)
    # check_awsapps(names, args.threads, args.nameserver)
    tasks.append(loop.run_in_executor(pool, check_s3_buckets, names, args.threads))
    tasks.append(loop.run_in_executor(pool, check_awsapps, names, args.threads, args.nameserver))
    await asyncio.gather(*tasks)
