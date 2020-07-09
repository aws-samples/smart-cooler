// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

exports.handler = (event, context, callback) => {

  var sandbox = event.sandbox;
  var chargePermissionId = event.chargePermissionId;
  var amount = event.amount;
  var merchantNote = event.merchantNote;
  var merchantStoerName = event.merchantStoerName;
  var merchantOrderId = event.merchantOrderId;

'use strict';

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
    'privateKey' : fs.readFileSync('./my_private_key.txt'),
    'region' : 'jp',
    'sandbox' : sandbox
};

function charge(payload, headers) {
    // console.log('-------------[Charge]-------------');
    client.apiCall({
        method: 'POST',
        urlFragment: 'in-store/v1/charge',
        payload: payload,
        headers: headers
    }).then(function (result) {
        console.log('statusCode=' + result.statusCode);
        const responseObject = JSON.parse(result.body);
        console.dir(responseObject, { depth: null });
        callback(null, responseObject);
    }).catch(err => {
        console.error('statusCode=' + err.statusCode);
        console.dir(JSON.parse(err.body), { depth: null });
        const errorObject = JSON.parse(err.body);
        callback(null, errorObject);    
    });
}

const client = new Client(configArgs);

const payload = {
    chargePermissionId  : chargePermissionId,
    // chargePermissionId  : $_POST["charge_id"],
    chargeReferenceId : "chargeRefId" + date,
    chargeTotal : {
      currencyCode : 'JPY',
    //   amount : $_POST["amount"]
      amount : amount,
    },
    metadata : {
        // merchantNote : json_encode($simulationString),
        merchantNote : merchantNote,
        // customInformation : 'In-store Ice Cream',
        communicationContext : {
            merchantStoreName : merchantStoerName,
            merchantOrderId : merchantOrderId
        }
    }
};

charge(payload, { } );
    

};
