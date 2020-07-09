'use strict';
// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

const fs = require('fs');

const Client = require('./client.js');

require('date-utils');
var dt = new Date();
var date = dt.toFormat("YYYYMMDDHH24MISS");
// console.log(date);

// var simulationString = ( 
//     status = { 
//     state : 'Declined', 
//     reasonCode : 'InvalidPaymentMethod',
//     // reasonCode : 'TransactionTimedOut'
//     // reasonCode : 'AmazonRejected'
//     // reasonCode : 'ProcessingFailure'
//     }
// );

const configArgs = {
    'publicKeyId' : 'AG23AX7S6ITTRB7UWFNIDM26',
    'privateKey' : fs.readFileSync('my_private_key.txt'),
    'region' : 'jp',
    'sandbox' : true
};

function charge(payload, headers) {
    console.log('-------------[Charge]-------------');
    client.apiCall({
        method: 'POST',
        urlFragment: 'in-store/v1/charge',
        payload: payload,
        headers: headers
    }).then(function (result) {
        console.log('SUCCESS: statusCode=' + result.statusCode);
        const responseObject = JSON.parse(result.body);
        console.dir(responseObject, { depth: null });
    }).catch(err => {
        console.error('ERROR: statusCode=' + err.statusCode);
        console.dir(JSON.parse(err.body), { depth: null });
    });
}

const client = new Client(configArgs);

const payload = {
    chargePermissionId  : "S03-9863575-1761733",
    // chargePermissionId  : $_POST["charge_id"],
    chargeReferenceId : "chargeRefId" + date,
    chargeTotal : {
      currencyCode : 'JPY',
    //   amount : $_POST["amount"]
      amount : 10,
    },
    metadata : {
        // merchantNote : json_encode($simulationString),
        // merchantNote : "メール表示テスト",
        customInformation : 'In-store Ice Cream',
        communicationContext : {
            merchantStoreName : 'In-store demo'
            // 'merchantOrderId' : '123789'
        }
    }
};

charge(payload, { } );