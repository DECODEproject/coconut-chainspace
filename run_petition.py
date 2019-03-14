# system
import requests
import json
import pprint

# chainspace
from chainspacecontract.examples.utils import *
import chainspacecontract as csc
# petlib
from petlib.bn import Bn


# coconut
import coconut.utils as cu
import coconut.scheme as cs

# petitions contracts
from contracts import petition
from contracts.petition import contract as petition_contract
from contracts.utils import *

debug = 0

pp = pprint.PrettyPrinter(indent=4)

# Petition Parameters
petition_UUID = Bn(1234)  # petition unique id (needed for crypto) - A BigNumber from Open SSL
options = ['YES', 'NO']

# petition owner parameters
# G = Group from the elliptic curve (default is openssl 713, NIST p224
# g = Generator for the group - this is a point on the ellptic curve (ECPt)
# hs =
# o = The order of the group

(G, g, hs, o) = pet_setup()


# Do some interesting things with EcPts:
# https://en.wikipedia.org/wiki/Elliptic_curve_point_multiplication
# https://stackoverflow.com/questions/5181320/under-what-circumstances-are-rmul-called
# Petlib overloads the multiplier operator "*" to allow multiplication of elliptic curve points by scalars
# which basically is like saying P * 3 == P + P + P
def debug_ec_point(ec_point):
    x, y = ec_point.get_affine()
    print("x = " + str(x))
    print("y = " + str(y))


def str_ec_pt(ec_pt):
    x, y = ec_pt.get_affine()
    return "EcPt(x = " + str(x) + ", y = " + str(y) + ")"


print("Type of g  : " + str(type(g)))
print("Add g to itself:")
debug_ec_point(g.pt_add(g))

print("2 * g:")
debug_ec_point(2 * g)

print("d.pt_double:")
debug_ec_point(g.pt_double())

# Example of el-gammal standard protocol:
#
# hide message m using alpha^k and beta^k where
# alpha is the primitive root of of a large prime and k is a random integer
# beta is equal to alpha^a where a is a secret known only to the reciever (receivers private key)
# primitive roots: http://mathworld.wolfram.com/PrimitiveRoot.html
# e.g. primitive roots of prim 13 are 2, 6, 7, 11

# Brooke chooses:
p = 13
alpha = 6
a = 3

# Brooke computes:
beta = pow(alpha, a)

# alpha, beta and p are public

# Abbie chooses:
k = 3

# Abbie wants to send the message m
m = 21

# Abbie computes:

alpha_k = pow(alpha, k)
beta_k_m = pow(beta, k) * m

print("\nEl-Gammal without elliptic curves...")
print("plaintext message(m) : " + str(m))

print("encrypted message: ")
print("alpha_k: " + str(alpha_k))
print("beta_k_m: " + str(beta_k_m))

# Abbie sends alpha_k and beta_k to brooke who can decrypt:
# See https://cse.unl.edu/~ssamal/crypto/EEECC.pdf

# (alpha_k ^ -a) * (beta_k * m) = m

# Brooke computes:

alpha_k_minus_a = pow(alpha_k, -a)
m_decrypted = int(alpha_k_minus_a * beta_k_m)

print("alpha_k_minus_a  : " + str(alpha_k_minus_a))
print("decrypted message: " + str(m_decrypted))
print("-- end el-gammal\n")

# Set up the petition


# Select a cryptographically secure random number less than the order for each of the owners


print("Petition Setup:")

# sk = secret key
# vk = verification key


t_owners = 2  # threshold number of owners
n_owners = 3  # total number of owners
v = [o.random() for _ in range(0, t_owners)]

print("threshold seeds for secret keys (v): " + str(v))

sk_owners = [cu.poly_eval(v, i) % o for i in range(1, n_owners + 1)]

print("\nSecret Keys of the petition owners: ")

for i in range(n_owners):
    print("sk[" + str(i) + "] : " + str(sk_owners[i]))

pk_owner = [xi * g for xi in sk_owners]

print("\nPublic keys of the petition owners: ")
for i in range(n_owners):
    print("pk[" + str(i) + "] : " + str_ec_pt(pk_owner[i]))

l = cu.lagrange_basis(range(1, t_owners + 1), o, 0)
aggr_pk_owner = cu.ec_sum([l[i] * pk_owner[i] for i in range(t_owners)])

print("\nAggregate public key for owners: " + str_ec_pt(aggr_pk_owner))

# coconut parameters

print("Coconut setup")
t, n = 4, 5  # threshold and total number of authorities
bp_params = cs.setup()  # bp system's parameters

(sk, vk) = cs.ttp_keygen(bp_params, t, n)  # authorities keys

print("\nSecret keys of the authorities (Credential issuers):")
for i in range(n):
    print("sk_auth[" + str(i) + "] : " + str(sk[i]))

print("\nVerification keys of the authorities (Credential issuers):")
for i in range(n):
    print("pk_auth[" + str(i) + "] : " + str(vk[i]))

aggr_vk = cs.agg_key(bp_params, vk, threshold=True)

print("\nAggregated Verification Key: " + str(aggr_vk))


def pp_json(json_str):
    pp.pprint(json.loads(json_str))


def pp_object(obj):
    pp.pprint(obj)


def post_transaction(transaction, path):
    transaction = csc.transaction_inline_objects(transaction)
    print("Posting transaction to " + path)
    if debug == 1:
        pp_object(transaction)

    response = requests.post(
        'http://127.0.0.1:5000/'
        + petition_contract.contract_name
        + path,
        json=transaction)
    return response


print("\n======== EXECUTING PETITION =========\n")


def sign_petition_crypto():
    global d, gamma, private_m, Lambda, ski, sigs_tilde, sigma_tilde, sigs, sigma
    # some crypto to get the credentials
    # ------------------------------------
    # This can be done with zencode "I create my new credential keypair"
    # Keypair for signer
    (d, gamma) = cs.elgamal_keygen(bp_params)
    private_m = [d]  # array containing the private attributes, in this case the private key
    Lambda = cs.prepare_blind_sign(bp_params, gamma, private_m)  # signer prepares a blind signature request from their private key
    # This would be done by the authority
    sigs_tilde = [cs.blind_sign(bp_params, ski, gamma, Lambda) for ski in sk]  # blind sign from each authority
    # back with the signer, unblind all the signatures, using the private key
    sigs = [cs.unblind(bp_params, sigma_tilde, d) for sigma_tilde in sigs_tilde]
    # aggregate all the credentials
    sigma = cs.agg_cred(bp_params, sigs)
    return (sigma, d)


with petition_contract.test_service():
    print("\npetition.init()")
    init_transaction = petition.init()
    token = init_transaction['transaction']['outputs'][0]

    post_transaction(init_transaction, "/init")

    create_transaction = petition.create_petition(
        (token,),
        None,
        None,
        petition_UUID,
        options,
        sk_owners[0],  # private key of the owner for signing
        aggr_pk_owner,  # public key of the owner
        t_owners,
        n_owners,
        aggr_vk  # aggregated verifier key
    )
    print("\npetition.create_petition()")

    post_transaction(create_transaction, "/create_petition")

    old_petition = create_transaction['transaction']['outputs'][1]
    old_list = create_transaction['transaction']['outputs'][2]

    for i in range(3):
        print("\npetition.sign() [" + str(i) + "]")

        (sigma, d) = sign_petition_crypto()

        print("\nAggregated credentials (sigma): " + str(sigma))
        # ------------------------------------

        print("\npetition.sign()")
        sign_transaction = petition.sign(
            (old_petition, old_list),
            None,
            None,
            d,
            sigma,
            aggr_vk,
            1
        )

        post_transaction(sign_transaction, "/sign")

        old_petition = sign_transaction['transaction']['outputs'][0]
        old_list = sign_transaction['transaction']['outputs'][1]


    # tally
    for i in range(t_owners):
        tally_transaction = petition.tally(
            (old_petition,),
            None,
            None,
            sk_owners[i],
            i,
            t_owners
        )

        post_transaction(tally_transaction, "/tally")

        old_petition = tally_transaction['transaction']['outputs'][0]

    # read
    read_transaction = petition.read(
        None,
        (old_petition,),
        None
    )

    post_transaction(read_transaction, "/read")


    print("\n\n==================== OUTCOME ====================\n")
    print('OUTCOME: ', json.loads(read_transaction['transaction']['returns'][0]))
    print("\n===================================================\n\n")

