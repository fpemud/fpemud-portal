#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import random
import crypto
from fwp_util import FwpUtil


class FwpCmd:

    def __init__(self, param):
        self.param = param

    def cmdInit(self):
        # generate CA certificate and private key
        caKey = crypto.PKey()
        caKey.generate_key(crypto.TYPE_RSA, 1024)

        caCert = crypto.X509()
        caCert.get_subject().CN = "fpemud-portal-ca"
        caCert.set_serial_number(random.randint(0, 65535))
        caCert.gmtime_adj_notBefore(0)
        caCert.gmtime_adj_notAfter(36500 * 24 * 3600)
        caCert.set_issuer(caCert.get_subject())
        caCert.set_pubkey(caKey)
        caCert.sign(caKey, 'sha1')

        # save certificate and private key
        FwpUtil.dumpCertAndKey(caCert, caKey, self.param.caCertFile, self.param.caPrivkeyFile)

        # generate certificate and private key
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 1024)

        cert = crypto.X509()
        cert.get_subject().CN = "fpemud-portal"
        cert.set_serial_number(random.randint(0, 65535))
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(36500 * 24 * 3600)
        cert.set_issuer(caCert.get_subject())
        cert.set_pubkey(k)
        cert.sign(caKey, 'sha1')

        # save certificate and private key
        FwpUtil.dumpCertAndKey(cert, k, self.param.certFile, self.param.privkeyFile)
