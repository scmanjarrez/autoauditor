package main

import (
	"fmt"
	"time"
	"strings"
	"crypto/sha256"
	"encoding/json"
	"encoding/base64"

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

type Disclosure struct {
	ObjectType       string `json:"docType"`
	DisclosureHash   string `json:"disclosureHash"`
	Date             string `json:"date"`
	Disclosure       string `json:"disclosure"`
}

type SmartContractHelp struct {
	Function    string `json:"function"`
	Description string `json:"description"`
	Arg         string `json:"arg"`
}

var tagSub = "subscriber"
var tagDisclosure = "disclosure"
var indexTagSubId = "tag~sid"
var indexOrgSubId = "organization~sid"
var indexTagDHash = "tag~dhash"
var indexDateDHash = "year~month~day~dhash"
var nullValue = []byte{0x00}  // 'nil' value delete key from state, so we need null character instead
var objTypeSub = "autoauditorSubscription"
var objTypeDisclosure = "autoauditorDisclosure"

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
			"Disclosure already in blockchain: %s",
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

func (s *SmartContract) PublishDisclosure(
	ctx contractapi.TransactionContextInterface) error {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 1 {
		return fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: Disclosure")
	}
	disclosureInp := params[0]
	disclosureHash := fmt.Sprintf("%x", sha256.Sum256([]byte(disclosureInp)))
	err := verifyData(ctx.GetStub(), disclosureHash)
	if err != nil {
		return err
	}
	date := fmt.Sprintf("%s", time.Now().Format("2006-01-02"))
	disclosure := &Disclosure{
		ObjectType: objTypeDisclosure,
		DisclosureHash: disclosureHash,
		Date: date,
		Disclosure: disclosureInp,
	}
	disclosureJSONAsBytes, err := json.Marshal(disclosure)
	if err != nil {
		return fmt.Errorf(
			"Failed to marshall disclosure: %s",
			err.Error())
	}
	err = putData(ctx.GetStub(), disclosureHash, disclosureJSONAsBytes)
	if err != nil {
		return err
	}
	tagBHashIndexKey, err := createCompKey(
		ctx.GetStub(), indexTagDHash,
		[]string{tagDisclosure, disclosureHash})
	if err != nil {
		return err
	}
	tagDateIndexKey, err := createCompKey(
		ctx.GetStub(), indexDateDHash,
		append(strings.Split(date, "-"), []string{disclosureHash}...))
	if err != nil {
		return err
	}
	err = putData(ctx.GetStub(), tagBHashIndexKey, nullValue)
	if err != nil {
		return err
	}
	err = putData(ctx.GetStub(), tagDateIndexKey, nullValue)
	if err != nil {
		return err
	}
	return nil
}

func (s *SmartContract) GetDisclosureByHash(
	ctx contractapi.TransactionContextInterface) (*Disclosure, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 1 {
		return nil, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: DisclosureHash")
	}
	disclosureHash := params[0]
	disclosureJSONAsBytes, err := getData(ctx.GetStub(), disclosureHash)
	if err != nil {
		return nil, err
	} else if disclosureJSONAsBytes == nil {
		return nil, fmt.Errorf(
			"Disclosure not present in blockchain: %s",
		disclosureHash)
	}
	disclosure := new(Disclosure)
	err = json.Unmarshal(disclosureJSONAsBytes, disclosure)
	if err != nil {
		return nil, fmt.Errorf(
			"Failed to unmarshall JSON: %s",
			err.Error())
	}
	return disclosure, nil
}

func (s *SmartContract) GetDisclosures(
	ctx contractapi.TransactionContextInterface) ([]Disclosure, error) {

	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexTagDHash, []string{tagDisclosure},
		[]string {""})
	if err != nil {
		return nil, err
	}
	defer resIterator.Close()
	results := []Disclosure{}
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
		dHash := compositeKeyParts[1]
		disclosureJSONAsBytes, err := getData(ctx.GetStub(), dHash)
		if err != nil {
			return nil, err
		}
		disclosure := new(Disclosure)
		err = json.Unmarshal(disclosureJSONAsBytes, disclosure)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to unmarshall JSON: %s",
				err.Error())
		}
		results = append(results, *disclosure)
	}
	if len(results) == 0 {
		return nil, fmt.Errorf("No results found")
	}
	return results, nil
}

func (s *SmartContract) GetTotalDisclosures(
	ctx contractapi.TransactionContextInterface) (int, error) {

	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexTagDHash, []string{tagDisclosure},
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

func (s *SmartContract) GetDisclosuresHash(
	ctx contractapi.TransactionContextInterface) ([]string, error) {

	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexTagDHash, []string{tagDisclosure},
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
		disclosureHash := compositeKeyParts[1]
		results = append(results, disclosureHash)
	}
	if len(results) == 0 {
		return nil, fmt.Errorf("No results found")
	}
	return results, nil
}

func (s *SmartContract) GetDisclosuresByDate(
	ctx contractapi.TransactionContextInterface) ([]Disclosure, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) < 1 || len(params) > 3 {
		return nil, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: YYYY [MM [DD]]")
	}
	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexDateDHash, params,
		[]string {""})
	if err != nil {
		return nil, err
	}
	defer resIterator.Close()
	results := []Disclosure{}
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
		disclosureHash := compositeKeyParts[3]
		disclosureJSONAsBytes, err := getData(ctx.GetStub(), disclosureHash)
		if err != nil {
			return nil, err
		}
		disclosure := new(Disclosure)
		err = json.Unmarshal(disclosureJSONAsBytes, disclosure)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to unmarshall JSON: %s",
				err.Error())
		}
		results = append(results, *disclosure)
	}
	if len(results) == 0 {
		return nil, fmt.Errorf("No results found")
	}
	return results, nil
}

func (s *SmartContract) GetTotalDisclosuresByDate(
	ctx contractapi.TransactionContextInterface) (int, error) {

		_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) < 1 || len(params) > 3 {
		return -1, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: YYYY [MM [DD]]")
	}
	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexDateDHash, params,
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

func (s *SmartContract) GetDisclosuresHashByDate(
	ctx contractapi.TransactionContextInterface) ([]string, error) {

			_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) < 1 || len(params) > 3 {
		return nil, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: YYYY [MM [DD]]")
	}
	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexDateDHash, params,
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
		disclosureHash := compositeKeyParts[3]
		results = append(results, disclosureHash)
	}
	if len(results) == 0 {
		return nil, fmt.Errorf(
			"No results found")
	}
	return results, nil
}

func (s *SmartContract) Help(
	ctx contractapi.TransactionContextInterface) []SmartContractHelp {

	results := []SmartContractHelp {
		{"Subscribe", "Subscribe to receive disclosures",
			"none"},
		{"Unsubscribe", "Unsubscribe from disclosures",
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
		{"PublishDisclosure",
			"Publish disclosure in blockchain",
			"Disclosure"},
		{"GetDisclosureByHash",
			"Query disclosure from a given Hash",
			"DisclosureHash"},
		{"GetDisclosures",
			"Query all disclosures present in blockchain",
			"none"},
		{"GetTotalDisclosures",
			"Query number of disclosures present in blockchain",
			"none"},
		{"GetDisclosuresHash",
			"Query all disclosures hash present in blockchain",
			"none"},
		{"GetDisclosuresByDate",
			"Query all disclosures from a given Date",
			"Date(YYYY [MM [DD]])"},
		{"GetTotalDisclosuresByDate",
			"Query number of disclosures from a given Date",
			"Date(YYYY [MM [DD]])"},
		{"GetDisclosuresHashByDate",
			"Query all disclosures hash from a given Date",
			"Date(YYYY [MM [DD]])"},
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
