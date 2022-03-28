package main

import (
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric-chaincode-go/shim"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

type SmartContract struct {
	contractapi.Contract
}

type Subscription struct {
	ObjectType   string `json:"docType"`
	SubscriberId string `json:"sid"`
	Organization string `json:"org"`
	Cert         string `json:"cert"`
}

type Blow struct {
	ObjectType string `json:"docType"`
	BlowHash   string `json:"bhash"`
	Blow       string `json:"blow"`
}

type SmartContractHelp struct {
	Function    string `json:"function"`
	Description string `json:"description"`
	Arg         string `json:"arg"`
}

var tagSub = "subscriber"
var tagBlow = "blow"
var indexTagSubId = "tag~sid"
var indexOrgSubId = "organization~sid"
var indexTagBHash = "tag~bhash"
var nullValue = []byte{0x00}  // 'nil' value delete key from state, so we need null character instead
var objTypeSub = "autoauditorSubscription"
var objTypeBlow = "autoauditorBlow"

func verifyData(
	stub shim.ChaincodeStubInterface,
	id string) (error) {

	subJSONAsBytes, err := stub.GetState(id)
	if err != nil {
		return fmt.Errorf(
			"Failed to retrieve blockchain data: %s: %s",
			id, err.Error())
	} else if subJSONAsBytes != nil {
		return fmt.Errorf(
			"Blow already in blockchain: %s",
			id)
	}
	return nil
}

func getData(
	stub shim.ChaincodeStubInterface,
	id string) ([]byte, error) {

	subJSONAsBytes, err := stub.GetState(id)
	if err != nil {
		return nil, fmt.Errorf(
			"Failed to retrieve blockchain data: %s: %s",
			id, err.Error())
	}
	return subJSONAsBytes, nil
}

func getDataByPartialCompKey(
	stub shim.ChaincodeStubInterface,
	index string, composite []string, params []string) (
	shim.StateQueryIteratorInterface, error) {

	resIterator, err := stub.GetStateByPartialCompositeKey(
		index, composite)
	if err != nil {
		return nil, fmt.Errorf(
			"Failed to retrieve blockchain data: %s",
			err.Error())
	} else if resIterator == nil {
		return nil, fmt.Errorf(
			"No results found with such criteria: %q",
			params)
	}
	return resIterator, nil
}

func putData(
	stub shim.ChaincodeStubInterface,
	id string, data []byte) (error) {

	err := stub.PutState(id, data)
	if err != nil {
		return fmt.Errorf(
			"Failed to store data in blockchain: %s",
			err.Error())
	}
	return nil
}

func delData(
	stub shim.ChaincodeStubInterface,
	id string) (error) {

	err := stub.DelState(id)
	if err != nil {
		return fmt.Errorf(
			"Failed to delete data from blockchain: %s",
			err.Error())
	}
	return nil
}

func createCompKey(
	stub shim.ChaincodeStubInterface,
	index string, composite []string) (string, error) {

	indexKey, err := stub.CreateCompositeKey(
		index, composite)
	if err != nil {
		return "", fmt.Errorf(
			"Failed to create composite key: %s: %s",
			index, err.Error())
	}
	return indexKey, nil
}

func (s *SmartContract) Subscribe(
	ctx contractapi.TransactionContextInterface) error {

	client := ctx.GetClientIdentity()
	cid, err := client.GetID()
	if err != nil {
		return fmt.Errorf(
			"Failed to retrieve ID from identity: %s",
			err.Error())
	}
	org, err := client.GetMSPID()
	if err != nil {
		return fmt.Errorf(
			"Failed to retrieve MSPID from identity: %s",
			err.Error())
	}
	cert, err := client.GetX509Certificate()
	if err != nil {
		return fmt.Errorf(
			"Failed to retrieve Cert from identity: %s",
			err.Error())
	}
	subJSONAsBytes, err := getData(ctx.GetStub(), cid)
	if err != nil {
		return err
	} else if subJSONAsBytes == nil {
		subscription := &Subscription{
			ObjectType: objTypeSub,
			SubscriberId: cid,
			Organization: org,
			Cert: base64.StdEncoding.EncodeToString(cert.Raw),
		}
		subJSONasBytes, err := json.Marshal(subscription)
		if err != nil {
			return fmt.Errorf(
				"Failed to marshall subscription: %s",
				err.Error())
		}
		err = putData(ctx.GetStub(), cid, subJSONasBytes)
		if err != nil {
			return err
		}
		tagSubIdIndexKey, err := createCompKey(
			ctx.GetStub(), indexTagSubId,
			[]string{tagSub, cid})
		if err != nil {
			return err
		}
		orgSubIdIndexKey, err := createCompKey(
			ctx.GetStub(), indexOrgSubId,
			[]string{org, cid})
		if err != nil {
			return err
		}
		err = putData(
			ctx.GetStub(), tagSubIdIndexKey, nullValue)
		if err != nil {
			return err
		}
		err = putData(
			ctx.GetStub(), orgSubIdIndexKey, nullValue)
		if err != nil {
			return err
		}
	}
	return nil
}

func (s *SmartContract) Unsubscribe(
	ctx contractapi.TransactionContextInterface) error {

	client := ctx.GetClientIdentity()
	cid, err := client.GetID()
	if err != nil {
		return fmt.Errorf(
			"Failed to get ID from identity: %s",
			err.Error())
	}
	org, err := client.GetMSPID()
	if err != nil {
		return fmt.Errorf(
			"Failed to get MSPID from identity: %s",
			err.Error())
	}
	subJSONAsBytes, err := getData(ctx.GetStub(), cid)
	if err != nil {
		return err
	} else if subJSONAsBytes == nil {
		return fmt.Errorf(
			"Failed to unsubscribe, already unsubscribed")
	}
	tagSubIdIndexKey, err := createCompKey(
		ctx.GetStub(), indexTagSubId,
		[]string{tagSub, cid})
	if err != nil {
		return err
	}
	orgSubIdIndexKey, err := createCompKey(
		ctx.GetStub(), indexOrgSubId,
		[]string{org, cid})
	if err != nil {
		return err
	}
	err = delData(ctx.GetStub(), tagSubIdIndexKey)
	if err != nil {
		return err
	}
	err = delData(ctx.GetStub(), orgSubIdIndexKey)
	if err != nil {
		return err
	}
	err = delData(ctx.GetStub(), cid)
	if err != nil {
		return err
	}
	return nil
}

func (s *SmartContract) GetSubscribers(
	ctx contractapi.TransactionContextInterface) ([]Subscription, error) {

	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexTagSubId, []string{tagSub},
		[]string{""})
	if err != nil {
		return nil, err
	}
	fmt.Println("hi")
	defer resIterator.Close()
	results := []Subscription{}
	for resIterator.HasNext() {
		fmt.Println("hu")
		response, err := resIterator.Next()
		if err != nil {
			return nil, err
		}
		_, compositeKeyParts, err := ctx.GetStub().SplitCompositeKey(
			response.Key)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to split composite key: %s",
				err.Error())
		}
		sid := compositeKeyParts[1]
		fmt.Println(sid)
		subJSONAsBytes, err := getData(ctx.GetStub(), sid)
		if err != nil {
			return nil, err
		}
		fmt.Println("h3")
		subscription := new(Subscription)
		err = json.Unmarshal(subJSONAsBytes, subscription)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to unmarshall JSON: %s",
				err.Error())
		}
		fmt.Println("ho")
		results = append(results, *subscription)
	}
	fmt.Println("what")
	fmt.Println(len(results))
	if len(results) == 0 {
		return nil, fmt.Errorf(
			"No results found")
	}
	return results, nil
}

func (s *SmartContract) GetTotalSubscribers(
	ctx contractapi.TransactionContextInterface) (int, error) {

	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexTagSubId, []string{tagSub},
		[]string {""})
	if err != nil {
		return -1, err
	}
	defer resIterator.Close()
	total := 0
	for resIterator.HasNext() {
		_, err := resIterator.Next()
		if err != nil {
			return -1, err
		}
		total++
	}
	if total == 0 {
		return -1, fmt.Errorf(
			"No results found")
	}
	return total, nil
}

func (s *SmartContract) GetSubscribersId(
	ctx contractapi.TransactionContextInterface) ([]string, error) {

	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexTagSubId, []string{tagSub},
		[]string{""})
	if err != nil {
		return nil, err
	}
	defer resIterator.Close()
	results := []string{}
	for resIterator.HasNext() {
		response, err := resIterator.Next()
		if err != nil {
			return nil, err
		}
		_, compositeKeyParts, err := ctx.GetStub().SplitCompositeKey(
			response.Key)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to split composite key: %s",
				err.Error())
		}
		sid := compositeKeyParts[1]
		results = append(results, sid)
	}
	if len(results) == 0 {
		return nil, fmt.Errorf(
			"No results found")
	}
	return results, nil
}

func (s *SmartContract) GetSubscriberById(
	ctx contractapi.TransactionContextInterface) (*Subscription, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 1 {
		return nil, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: SubscriberID")
	}
	sid := params[0]
	subJSONAsBytes, err := getData(ctx.GetStub(), sid)
	if err != nil {
		return nil, err
	} else if subJSONAsBytes == nil {
		return nil, fmt.Errorf(
			"Subscriber not present in blockchain: %s",
		sid)
	}
	subscription := new(Subscription)
	err = json.Unmarshal(subJSONAsBytes, subscription)
	if err != nil {
		return nil, fmt.Errorf(
			"Failed to unmarshall JSON: %s",
			err.Error())
	}
	return subscription, nil
}

func (s *SmartContract) GetCertificateById(
	ctx contractapi.TransactionContextInterface) (string, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 1 {
		return "", fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: SubscriberId")
	}
	sid := params[0]
	subJSONAsBytes, err := getData(ctx.GetStub(), sid)
	if err != nil {
		return "", err
	} else if subJSONAsBytes == nil {
		return "", fmt.Errorf(
			"No result found with such criteria. Check parameter: '%s'",
			sid)
	}
	subscription := new(Subscription)
	err = json.Unmarshal(subJSONAsBytes, subscription)
	if err != nil {
		return "", fmt.Errorf(
			"Failed to unmarshall JSON: %s",
			err.Error())
	}
	return subscription.Cert, nil
}

func (s *SmartContract) GetSubscribersByOrganization(
	ctx contractapi.TransactionContextInterface) ([]Subscription, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 1 {
		return nil, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: OrgName")
	}
	org := params[0]
	resIterator, err := getDataByPartialCompKey(ctx.GetStub(),
		indexOrgSubId, []string{org}, params)
	if err != nil {
		return nil, err
	}
	defer resIterator.Close()
	results := []Subscription{}
	for resIterator.HasNext() {
		response, err := resIterator.Next()
		if err != nil {
			return nil, err
		}
		_, compositeKeyParts, err := ctx.GetStub().SplitCompositeKey(
			response.Key)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to split composite key: %s",
				err.Error())
		}
		sid := compositeKeyParts[1]
		subJSONAsBytes, err := getData(ctx.GetStub(), sid)
		if err != nil {
			return nil, err
		}
		subscription := new(Subscription)
		err = json.Unmarshal(subJSONAsBytes, subscription)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to unmarshall JSON: %s",
				err.Error())
		}
		results = append(results, *subscription)
	}
	if len(results) == 0 {
		return nil, fmt.Errorf(
			"No results found with such criteria. Check parameter: '%s'",
			org)
	}
	return results, nil
}

func (s *SmartContract) GetTotalSubscribersByOrganization(
	ctx contractapi.TransactionContextInterface) (int, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 1 {
		return -1, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: OrgName")
	}
	org := params[0]
	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexOrgSubId, []string{org}, params)
	if err != nil {
		return -1, err
	}
	defer resIterator.Close()
	total := 0
	for resIterator.HasNext() {
		_, err := resIterator.Next()
		if err != nil {
			return -1, err
		}
		total++
	}
	if total == 0 {
		return -1, fmt.Errorf(
			"No results found with such criteria. Check parameters: %q",
			params)
	}
	return total, nil
}

func (s *SmartContract) GetSubscribersIdByOrganization(
	ctx contractapi.TransactionContextInterface) ([]string, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 1 {
		return nil, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: OrgName")
	}
	org := params[0]
	resIterator, err := getDataByPartialCompKey(ctx.GetStub(),
		indexOrgSubId, []string{org}, params)
	if err != nil {
		return nil, err
	}
	defer resIterator.Close()
	results := []string{}
	for resIterator.HasNext() {
		response, err := resIterator.Next()
		if err != nil {
			return nil, err
		}
		_, compositeKeyParts, err := ctx.GetStub().SplitCompositeKey(
			response.Key)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to split composite key: %s",
				err.Error())
		}
		sid := compositeKeyParts[1]
		results = append(results, sid)
	}
	if len(results) == 0 {
		return nil, fmt.Errorf(
			"No results found with such criteria. Check parameter: '%s'",
			org)
	}
	return results, nil
}

func (s *SmartContract) StoreBlow(
	ctx contractapi.TransactionContextInterface) error {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 1 {
		return fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: Blow")
	}
	blowInp := params[0]
	blowHash := fmt.Sprintf("%x", sha256.Sum256([]byte(blowInp)))
	err := verifyData(ctx.GetStub(), blowHash)
	if err != nil {
		return err
	}
	blow := &Blow{
		ObjectType: objTypeBlow,
		BlowHash: blowHash,
		Blow: blowInp,
	}
	blowJSONAsBytes, err := json.Marshal(blow)
	if err != nil {
		return fmt.Errorf(
			"Failed to marshall blow: %s",
			err.Error())
	}
	err = putData(ctx.GetStub(), blowHash, blowJSONAsBytes)
	if err != nil {
		return err
	}
	tagBHashIndexKey, err := createCompKey(
		ctx.GetStub(), indexTagBHash,
		[]string{tagBlow, blowHash})
	if err != nil {
		return err
	}
	err = putData(ctx.GetStub(), tagBHashIndexKey, nullValue)
	if err != nil {
		return err
	}
	return nil
}

func (s *SmartContract) GetBlowByHash(
	ctx contractapi.TransactionContextInterface) (*Blow, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 1 {
		return nil, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: BlowHash")
	}
	blowHash := params[0]
	blowJSONAsBytes, err := getData(ctx.GetStub(), blowHash)
	if err != nil {
		return nil, err
	} else if blowJSONAsBytes == nil {
		return nil, fmt.Errorf(
			"Blow not present in blockchain: %s",
		blowHash)
	}
	blow := new(Blow)
	err = json.Unmarshal(blowJSONAsBytes, blow)
	if err != nil {
		return nil, fmt.Errorf(
			"Failed to unmarshall JSON: %s",
			err.Error())
	}
	return blow, nil
}

func (s *SmartContract) GetBlows(
	ctx contractapi.TransactionContextInterface) ([]Blow, error) {

	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexTagBHash, []string{tagBlow},
		[]string {""})
	if err != nil {
		return nil, err
	}
	defer resIterator.Close()
	results := []Blow{}
	for resIterator.HasNext() {
		response, err := resIterator.Next()
		if err != nil {
			return nil, err
		}
		_, compositeKeyParts, err := ctx.GetStub().SplitCompositeKey(
			response.Key)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to split composite key: %s",
				err.Error())
		}
		bHash := compositeKeyParts[1]
		blowJSONAsBytes, err := getData(ctx.GetStub(), bHash)
		if err != nil {
			return nil, err
		}
		blow := new(Blow)
		err = json.Unmarshal(blowJSONAsBytes, blow)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to unmarshall JSON: %s",
				err.Error())
		}
		results = append(results, *blow)
	}
	if len(results) == 0 {
		return nil, fmt.Errorf("No results found")
	}
	return results, nil
}

func (s *SmartContract) GetTotalBlows(
	ctx contractapi.TransactionContextInterface) (int, error) {

	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexTagBHash, []string{tagBlow},
		[]string{""})
	if err != nil {
		return -1, err
	}
	defer resIterator.Close()
	total := 0
	for resIterator.HasNext() {
		_, err := resIterator.Next()
		if err != nil {
			return -1, err
		}
		total++
	}
	if total == 0 {
		return -1, fmt.Errorf("No results found")
	}
	return total, nil
}

func (s *SmartContract) GetBlowsHash(
	ctx contractapi.TransactionContextInterface) ([]string, error) {

	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexTagBHash, []string{tagBlow},
		[]string {""})
	if err != nil {
		return nil, err
	}
	defer resIterator.Close()
	results := []string{}
	for resIterator.HasNext() {
		response, err := resIterator.Next()
		if err != nil {
			return nil, err
		}
		_, compositeKeyParts, err := ctx.GetStub().SplitCompositeKey(
			response.Key)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to split composite key: %s",
				err.Error())
		}
		bHash := compositeKeyParts[1]
		results = append(results, bHash)
	}
	if len(results) == 0 {
		return nil, fmt.Errorf("No results found")
	}
	return results, nil
}

func (s *SmartContract) Help(
	ctx contractapi.TransactionContextInterface) []SmartContractHelp {

	results := []SmartContractHelp {
		{"Subscribe", "Subscribe to receive blows",
			"none"},
		{"Unsubscribe", "Unsubscribe from blows",
			"none"},
		{"GetSubscribers",
			"Query all subcribers present in blockchain",
			"none"},
		{"GetTotalSubscribers",
			"Query number of subscribers present in blockchain",
			"none"},
		{"GetSubcribersId",
			"Query all subscribers Id present in blockchain",
			"none"},
		{"GetSubscriberById",
			"Query subcriber from a given Id",
			"SubscriberId"},
		{"GetCertificateById",
			"Query subscriber certificate from a given Id",
			"SubscriberId"},
		{"GetSubscribersByOrganization",
			"Query all subscribers from a given Organization",
			"OrgName"},
		{"GetTotalSubscribersByOrganization",
			"Query number of subscribers from a given Organization",
			"OrgName"},
		{"GetSubscribersIdByOrganization",
			"Query all subscribers Id from a given Organization",
			"OrgName"},
		{"StoreBlow",
			"Store blow in blockchain",
			"Blow"},
		{"GetBlowByHash",
			"Query blow from a given Hash",
			"BlowHash"},
		{"GetBlows",
			"Query all blows present in blockchain",
			"none"},
		{"GetTotalBlows",
			"Query number of blows present in blockchain",
			"none"},
		{"GetBlowsHash",
			"Query all blows hash present in blockchain",
			"none"},
		{"Help",
			"Show smart contract available functions",
			"none"},
	}
	return results
}

func main() {
	chaincode, err := contractapi.NewChaincode(new(SmartContract))
	if err != nil {
		fmt.Printf("Error creating whistleblower chaincode: %s", err.Error())
		return
	}
	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting whistleblower chaincode: %s", err.Error())
	}
}
