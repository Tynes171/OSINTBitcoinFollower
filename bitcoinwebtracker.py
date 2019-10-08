import argparse
import requests
import networkx


webhose_access_token = "938cda78-61e0-46e3-a230-565fd8d8ecb2"


blacklist = ["4a6kzlzytb4ksafk.onion", "blockchainbdgpzk.onion"]


webhose_base_url = "http://webhose.io"
webhose_darkweb_url = "/darkFilter?token=%s&format=json&q=" %webhose_access_token


block_explorer_url = "https://blockexplorer.com/api/addrs/"



parser = argparse.ArgumentParser(description = "Collect and visualize Bitcoin transactions")


#parser.add_argument("--graph",help="Output filename of the graph file. Example: bitcoin.gexf",default="bitcoingraph.gexf")
parser.add_argument("-a","--address", help="A bitcoin address to begin the search on.",)

args = parser.parse_args()


bitcoin_address = args.address
#graph = args['graph']

def get_all_transactions(bitcoin_address):

    transactions = []
    from_number = 0
    to_number = 50

    block_explorer_url_full = block_explorer_url + bitcoin_address + "/txs?from=%d&to=%d" % (from_number,to_number)

    response = requests.get(block_explorer_url_full)
    response.raise_for_status()

    try:
        results = response.json()

    except Exception as e:
        print e
        print "[!] Error retrieving bitcoin transactions. Please re-run this script."
        return transactions

    if results['totalItems'] == 0:
        print "[*] no transactions for %s" %bitcoin_address
        return transactions

    transactions.extend(results['items'])

    while len(transactions) < results['totalItems']:

        from_number += 50
        to_number += 50

        block_explorer_url_full = block_explorer_url + bitcoin_address + "/txs?from=%d&to=%d" % (from_number,to_number)

        response = requests.get(block_explorer_url_full)

        results = response.json()


        transactions.extend(results['items'])

    print "[*] Retrieved %d bitcoin transactions." %len(transactions)

    return transactions


def get_unique_bitcoin_addresses(transaction_list):

    bitcoin_addresses = []

    for transaction in transaction_list:

        if transaction['vin'][0]['addr'] not in bitcoin_addresses:
            bitcoin_addresses.append(transaction['vin'][0]['addr'])


        for receiving_side in transaction['vout']:

            if receiving_side['scriptPubKey'].has_key("addresses"):

                for address in receiving_side['scriptPubKey']['addresses']:

                    if address not in bitcoin_addresses:

                        bitcoin_addresses.append(address)


    print "[*] Identified %d unique bitcoin addresses. " %len(bitcoin_addresses)

    return bitcoin_addresses

                        
def search_webhose(bitcoin_addresses):

    bitcoin_to_hidden_services = {}
    count = 1


    for bitcoin_address in bitcoin_addresses:

        print "[*] Searching %d of %d bitcoin addresses. " % (count, len(bitcoin_addresses))
        

        search_url = webhose_base_url + webhose_darkweb_url + bitcoin_address

        response = requests.get(search_url)

        result = response.json()



        while result['totalResults'] > 0:

            for search_result in result['darkposts']:


                if not bitcoin_to_hidden_services.has_key(bitcoin_address):
                    bitcoin_to_hidden_services[bitcoin_address] = []

                if search_result['source']['site'] not in bitcoin_to_hidden_services[bitcoin_address]:

                    bitcoin_to_hidden_services[bitcoin_address].append(search_result['source']['site'])
                    
            if result['totalResults'] <= 10:
                break

            query = "%s" %bitcoin_address


            for hidden_service in bitcoin_to_hidden_services[bitcoin_address]:

                query += " -site:%s" %hidden_service



            for hidden_service in blacklist:

                query += " -site:%s" %hidden_service


            search_url = webhose_base_url + webhose_darkweb_url + query


            response = requests.get(search_url)

            result = response.json()


        if bitcoin_to_hidden_services.has_key(bitcoin_address):

            print "[*] Discovered %d hidden services connected to %s" % (len(bitcoin_to_hidden_services[bitcoin_address]), bitvoin_address)


        count += 1


    return bitcoin_to_hidden_services


	
#
# Graph all of the Bitcoin transactions
#
def build_graph(source_bitcoin_address,transaction_list,hidden_services):
    
    graph = networkx.DiGraph()
    
    # graph the transactions by address
    for transaction in transaction_list:
        
        # check the sending address
        sender = transaction['vin'][0]['addr']
    
        if sender == source_bitcoin_address:
            graph.add_node(sender,{"type":"Target Bitcoin Wallet"})
        else:
            graph.add_node(sender,{"type":"Bitcoin Wallet"})
        
      
        # walk through all recipients and check each address
        for receiving_side in transaction['vout']:
    
            if receiving_side['scriptPubKey'].has_key("addresses"):
                for address in receiving_side['scriptPubKey']['addresses']:
                    
                    if address == source_bitcoin_address:
                        graph.add_node(address,{"type":"Target Bitcoin Address"})
                    else:
                        graph.add_node(address,{"type":"Bitcoin Address"})
                    
                    graph.add_edge(sender,address)
        
    for bitcoin_address in hidden_services:
        
        for hidden_service in hidden_services[bitcoin_address]:
            
            if hidden_service not in blacklist:
                graph.add_node(hidden_service,{"type":"Hidden Service"})
                graph.add_edge(bitcoin_address,hidden_service)
    
    
    # write out the graph
    networkx.write_gexf(graph,graph_file)
    
    return




print "[*] Retrieving all transactions from the blockchain for %s" % bitcoin_address
 
transaction_list = get_all_transactions(bitcoin_address)
 
if len(transaction_list) > 0:
    
    # get all of the unique bitcoin addresses
    bitcoin_addresses = get_unique_bitcoin_addresses(transaction_list)
    
    # now search Webhose for all addresses looking
    # for hidden services
    hidden_services   = search_webhose(bitcoin_addresses)
 
    # graph the bitcoin transactions
    #build_graph(bitcoin_address,transaction_list, hidden_services)
    
    print "[*] Done! Open the graph file and happy hunting!"


                
