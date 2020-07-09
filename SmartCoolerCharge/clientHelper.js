'use strict';
// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

const constants = require('./constants.js');
const crypto = require('crypto');
const request = require('request');

/* Expected options:
       options.method
       options.urlFragment
       options.payload
       options.headers
*/
exports.signHeaders = function (configArgs, options) {
    const headers = {};

    if ((options.headers !== null) && (options.headers !== undefined)) {
        Object.keys(options.headers).forEach(item => headers[item] = options.headers[item]);
    }

    headers['x-amz-pay-region'] = configArgs.region;
    headers['x-amz-pay-host'] =  constants.REGION_MAP[configArgs.region.toLowerCase()];
    headers['x-amz-pay-date'] = getTimestamp();
    headers['content-type'] =  'application/json';
    headers['accept'] = 'application/json';
    headers['user-agent'] = `amazon-pay-sdk-nodejs/${constants.VERSION} (JS/${process.versions.node}; ${process.platform})`;

    const lowercaseSortedHeaderKeys = Object.keys(headers).sort(function (a, b) {
        return a.toLowerCase().localeCompare(b.toLowerCase());
    });

    let signedHeaders = '';
    lowercaseSortedHeaderKeys.forEach(item => signedHeaders += item.toLowerCase() + ';');
    signedHeaders = signedHeaders.slice(0, -1); // remove trailing semicolon

    let payload = options.payload;
    if ((payload === null) || (payload === undefined) || (options.urlFragment.includes('/account-management/v1/accounts'))) {
        payload = ''; // do not sign payload for payment critical data APIs
    }

    let canonicalRequest = options.method + '\n/' + options.urlFragment + '\n\n';
    lowercaseSortedHeaderKeys.forEach(item => canonicalRequest += item.toLowerCase() + ':' + headers[item] + '\n');
    canonicalRequest += '\n' + signedHeaders + '\n' + crypto.createHash('SHA256').update(payload).digest('hex');
//    console.log('\nCANONICAL REQUEST (dashes added for clarity only):\n---\n' + canonicalRequest + '\n---\n');

    const stringToSign = constants.AMAZON_SIGNATURE_ALGORITHM + '\n' +
        crypto.createHash('SHA256').update(canonicalRequest).digest('hex');

//    console.log('STRING TO SIGN (dashes added for clarity only):\n---\n' + stringToSign + '\n---\n');

    const signature = sign(configArgs.privateKey, stringToSign);
//    console.log('BASE64 ENCODED SIGNATURE:\n' + signature + '\n');

    headers['authorization'] = constants.AMAZON_SIGNATURE_ALGORITHM
        + ' PublicKeyId=' + configArgs['publicKeyId']
        + ', SignedHeaders=' + signedHeaders
        + ', Signature=' + signature;

   return headers;
}

function getTimestamp() {
    const date = new Date();
    return date.toISOString().split('.')[0] + 'Z';
}

function sign(privateKey, stringToSign) {
    const sign = crypto.createSign('RSA-SHA256').update(stringToSign);
    return sign.sign({
        key: privateKey,
        padding: crypto.constants.RSA_PKCS1_PSS_PADDING,
        saltLength: 20
    }, 'base64');
}

exports.retryLogic = function (options, count) {
    const response = this.sendRequest(options, count);

    if (count > constants.RETRIES) {
        return response.then(function (result) {
            return result;
        }).catch(err => {
            return Promise.reject(err);
        });
    }

    return response.then(function (result) {
        return result;
    }).catch(err => {
        if ((response.statusCode == 429) || (response.statusCode >= 500 && response.statusCode < 600)) {
            return this.retryLogic(options, count += 1);
        } else {
            return Promise.reject(err);
        }
    })
}

exports.sendRequest = function (options, count) {
    const delayTime = count === 1 ? 0 : (2 ** (count - 1)) * 1000;

    return new Promise(function (resolve, reject) {
        setTimeout(function () {
            request(options, function (err, response, body) {
                if (err) {
                    reject(err);
                } else if (response.statusCode >= 400 && response.statusCode < 600) {
                    reject(response);
                } else {
                    resolve(response);
                }
            });
        }, delayTime);
    });
}

exports.invokeApi = function (configArgs, apiOptions) {

    const options = {
        method: apiOptions.method,
        json: false,
        headers: apiOptions.headers,
        url: 'https://' + constants.REGION_MAP[configArgs.region.toLowerCase()] + '/' + apiOptions.urlFragment,
        body: apiOptions.payload
    };

    const count = 1;
    const response = this.retryLogic(options, count);

    return response;
}

exports.prepareOptions = function (configArgs, options) {
    if ((options.headers === null) || (options.headers === undefined)) {
        options.headers = {};
    }

    // if user doesn't pass in a string, assume it's a JS object and convert it to a JSON string
    if (!((typeof options.payload === 'string') || (options.payload instanceof String))) {
        options.payload = JSON.stringify(options.payload);
    }

    if ((configArgs['sandbox'] === true) || (configArgs['sandbox'] === 'true')) {
        options.urlFragment = 'sandbox/' + options.urlFragment;
    } else {
        options.urlFragment = 'live/' + options.urlFragment;
    }
    return options;
}
