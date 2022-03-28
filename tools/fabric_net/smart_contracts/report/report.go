package main

import (
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric-chaincode-go/shim"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

type SmartContract struct {
	contractapi.Contract
}

var publicCollection = "autoauditorReports"
var privateCollection = "autoauditorPReports"
var transStore = "report_st"
var transDelete = "report_del"
var tagRep = "report"
var indexTagRepId = "tag~rid"
var indexOrgRepId = "organization~rid"
var indexDateOrgRepId = "date~organization~rid"
// 'nil' value delete key from state, so we need null character instead
var nullValue = []byte {0x00}
var objTypeRep = "autoauditorReport"

type Report struct {
	ObjectType   string `json:"docType"`
	RepId        string `json:"rid"`
	Organization string `json:"org"`
	Date         string `json:"date"`
	TotalVuln    int    `json:"nVuln"`
	AuditReport  string `json:"report"`
}

type SmartContractHelp struct {
	Function    string `json:"function"`
	Description string `json:"description"`
	Transient   string `json:"transient"`
	Arg         string `json:"arg"`
	OptArgs     string `json:"optargs"`
}

type reportTransInput struct {
	RepId        string `json:"rid"`
	Date         string `json:"date"`
	NVuln        int    `json:"nVuln"`
	Private      bool   `json:"private"`
	Report       string `json:"report"`
}

type reportTransInputDel struct {
	RepId string `json:"rid"`
}

func getCollection(collect string) (string, error) {
	switch collect {
	case "public":
		return publicCollection, nil
	case "private":
		return privateCollection, nil
	default:
		return "", fmt.Errorf(
			"Collection does not exist: %s. " +
				"Choose between public or private",
			collect)
	}
}

func verifyData(
	stub shim.ChaincodeStubInterface,
	id string, collect string) (error) {

	repJSONAsBytes, err := stub.GetPrivateData(collect, id)
	if err != nil {
		return fmt.Errorf(
			"Failed to retrieve blockchain data: %s: %s",
			id, err.Error())
	} else if repJSONAsBytes != nil {
		return fmt.Errorf(
			"Report already in blockchain: %s",
			id)
	}
	return nil
}

func getData(
	stub shim.ChaincodeStubInterface,
	id string, collect string) ([]byte, error) {

	repJSONAsBytes, err := stub.GetPrivateData(collect, id)
	if err != nil {
		return nil, fmt.Errorf(
			"Failed to retrieve blockchain data: %s: %s",
			id, err.Error())
	} else if repJSONAsBytes == nil {
		return nil, fmt.Errorf(
			"No result found with such criteria: %s",
			id)
	}
	return repJSONAsBytes, nil
}

func getDataHighestPermission(
	stub shim.ChaincodeStubInterface,
	id string) ([]byte, error) {

	repJSONAsBytes, err := stub.GetPrivateData(privateCollection, id)
	if err != nil || repJSONAsBytes == nil {
		repJSONAsBytes, err = stub.GetPrivateData(publicCollection, id)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to retrieve blockchain data: %s: %s",
				id, err.Error())
		} else if repJSONAsBytes == nil {
			return nil, fmt.Errorf(
				"No result found with such criteria: %s",
				id)
		}
	}
	return repJSONAsBytes, nil
}

func getDataByPartialCompKey(
	stub shim.ChaincodeStubInterface,
	index string, composite []string, collect string, params []string) (
	shim.StateQueryIteratorInterface, error) {

	resIterator, err := stub.GetPrivateDataByPartialCompositeKey(
		collect, index, composite)
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
	id string, collect string, data []byte) (error) {

	err := stub.PutPrivateData(collect, id, data)
	if err != nil {
		return fmt.Errorf(
			"Failed to store data in blockchain: %s",
			err.Error())
	}
	return nil
}

func delData(
	stub shim.ChaincodeStubInterface,
	id string, collect string) (error) {

	err := stub.DelPrivateData(collect, id)
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

func (s *SmartContract) StoreReport(
	ctx contractapi.TransactionContextInterface) error {

	transMap, err := ctx.GetStub().GetTransient()
	if err != nil {
		return fmt.Errorf(
			"Failed to retrieve transient data: %s",
			err.Error())
	}
	transJSONAsBytes, ok := transMap[transStore]
	if !ok {
		return fmt.Errorf(
			"Data '%s' not found in transient map",
			transStore)
	}
	if len(transJSONAsBytes) == 0 {
		return fmt.Errorf(
			"Value '%s' in transient map must be " +
				"a non-empty JSON string",
			transStore)
	}
	var repInput reportTransInput
	err = json.Unmarshal(transJSONAsBytes, &repInput)
	if err != nil {
		return fmt.Errorf(
			"Failed to unmarshall JSON: %s",
			err.Error())
	}
	if len(repInput.RepId) == 0 {
		return fmt.Errorf(
			"Field 'rid' must be a non-empty string")
	}
	if len(repInput.Date) == 0 {
		return fmt.Errorf(
			"Field 'date' must be a non-empty string")
	}
	if repInput.NVuln <= 0 {
		return fmt.Errorf(
			"Field 'nVuln' must be a positive integer")
	}
	if len(repInput.Report) == 0 {
		return fmt.Errorf(
			"Field 'report' must be a non-empty string")
	}
	collect := publicCollection
	if repInput.Private {
		collect = privateCollection
	}
	err = verifyData(ctx.GetStub(), repInput.RepId, collect)
	if err != nil {
		return err
	}
	user := ctx.GetClientIdentity()
	org, err := user.GetMSPID()
	if err != nil {
		return fmt.Errorf(
			"Failed to retrieve MSPID from identity: %s",
			err.Error())
	}
	report := &Report {
		ObjectType:   objTypeRep,
		RepId:        repInput.RepId,
		Organization: org,
		Date:         repInput.Date,
		TotalVuln:    repInput.NVuln,
		AuditReport:  repInput.Report,
	}
	repJSONAsBytes, err := json.Marshal(report)
	if err != nil {
		return fmt.Errorf(
			"Failed to marshall report: %s",
			err.Error())
	}
	err = putData(
		ctx.GetStub(), repInput.RepId, collect, repJSONAsBytes)
	if err != nil {
		return err
	}
	if collect == publicCollection {
		tagRepIdIndexKey, err := createCompKey(
			ctx.GetStub(), indexTagRepId,
			[]string {tagRep, repInput.RepId})
		if err != nil {
			return err
		}
		orgRepIdIndexKey, err := createCompKey(
			ctx.GetStub(), indexOrgRepId,
			[]string {org, repInput.RepId})
		if err != nil {
			return err
		}
		date := repInput.Date[:7]
		dateOrgRepIdIndexKey, err := createCompKey(
			ctx.GetStub(), indexDateOrgRepId,
			[]string {date, org, repInput.RepId})
		if err != nil {
			return err
		}
		err = putData(
			ctx.GetStub(), tagRepIdIndexKey, collect, nullValue)
		if err != nil {
			return err
		}
		err = putData(
			ctx.GetStub(), orgRepIdIndexKey, collect, nullValue)
		if err != nil {
			return err
		}
		err = putData(
			ctx.GetStub(), dateOrgRepIdIndexKey, collect, nullValue)
		if err != nil {
			return err
		}
	}
	return nil
}

func (s *SmartContract) DeleteReport(
	ctx contractapi.TransactionContextInterface) error {

	transMap, err := ctx.GetStub().GetTransient()
	if err != nil {
		return fmt.Errorf(
			"Failed to retrieve transient data: %s",
			err.Error())
	}
	transDelJSONAsBytes, ok := transMap[transDelete]
	if !ok {
		return fmt.Errorf(
			"Data '%s' not found in transient map",
			transDelete)
	}
	if len(transDelJSONAsBytes) == 0 {
		return fmt.Errorf(
			"Value '%s' in transient map must be " +
				"a non-empty JSON string",
			transDelete)
	}
	var repInputDel reportTransInputDel
	err = json.Unmarshal(transDelJSONAsBytes, &repInputDel)
	if err != nil {
		return fmt.Errorf(
			"Failed to unmarshall JSON: %s",
			err.Error())
	}
	if len(repInputDel.RepId) == 0 {
		return fmt.Errorf(
			"Field 'rid' must be a non-empty string")
	}
	repJSONAsBytes, err := getData(
		ctx.GetStub(), repInputDel.RepId, publicCollection)
	if err != nil {
		return err
	}
	var repToDel Report
	err = json.Unmarshal(repJSONAsBytes, &repToDel)
	if err != nil {
		return fmt.Errorf(
			"Failed to unmarshall JSON: %s",
			err.Error())
	}
	tagRepIdIndexKey, err := createCompKey(
		ctx.GetStub(), indexTagRepId,
		[]string {tagRep, repToDel.RepId})
	if err != nil {
		return err
	}
	orgRepIdIndexKey, err := createCompKey(
		ctx.GetStub(), indexOrgRepId,
		[]string {repToDel.Organization, repToDel.RepId})
	if err != nil {
		return err
	}
	date := repToDel.Date[:7]
	dateOrgRepIdIndexKey, err := createCompKey(
		ctx.GetStub(), indexDateOrgRepId,
		[]string {date, repToDel.Organization, repToDel.RepId})
	if err != nil {
		return err
	}
	err = delData(
		ctx.GetStub(), tagRepIdIndexKey, publicCollection)
	if err != nil {
		return err
	}
	err = delData(
		ctx.GetStub(), orgRepIdIndexKey, publicCollection)
	if err != nil {
		return err
	}
	err = delData(
		ctx.GetStub(), dateOrgRepIdIndexKey, publicCollection)
	if err != nil {
		return err
	}
	err = delData(
		ctx.GetStub(), repInputDel.RepId, publicCollection)
	if err != nil {
		return err
	}
	err = delData(
		ctx.GetStub(), repInputDel.RepId, privateCollection)
	if err != nil {
		return err
	}
	return nil
}

func (s *SmartContract) GetReports(
	ctx contractapi.TransactionContextInterface) ([]Report, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 0 && len(params) != 1 {
		return nil, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: [public|private]")
	}
	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexTagRepId, []string {tagRep},
		publicCollection, params)
	if err != nil {
		return nil, err
	}
	defer resIterator.Close()
	var repJSONAsBytes []byte
	results := []Report {}
	for resIterator.HasNext() {
		resp, err := resIterator.Next()
		if err != nil {
			return nil, err
		}
		_, compKeyParts, err := ctx.GetStub().SplitCompositeKey(resp.Key)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to split composite key: %s",
				err.Error())
		}
		rid := compKeyParts[1]
		if len(params) == 0 {
			repJSONAsBytes, err = getDataHighestPermission(ctx.GetStub(), rid)
			if err != nil {
				return nil, err
			}
		} else {
			collect, err := getCollection(params[0])
			if err != nil {
				return nil, err
			}
			repJSONAsBytes, err = getData(ctx.GetStub(), rid, collect)
			if err != nil {
				return nil, err
			}
		}
		report := new(Report)
		err = json.Unmarshal(repJSONAsBytes, report)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to unmarshall JSON: %s",
				err.Error())
		}
		results = append(results, *report)
	}
	if len(results) == 0 {
		return nil, fmt.Errorf(
			"No results found with such criteria. Check parameters: %q",
			params)
	}
	return results, nil
}

func (s *SmartContract) GetTotalReports(
	ctx contractapi.TransactionContextInterface) (int, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexTagRepId, []string {tagRep},
		publicCollection, params)
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

func (s *SmartContract) GetReportsId(
	ctx contractapi.TransactionContextInterface) ([]string, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexTagRepId, []string {tagRep},
		publicCollection, params)
	if err != nil {
		return nil, err
	}
	defer resIterator.Close()
	results := []string {}
	for resIterator.HasNext() {
		resp, err := resIterator.Next()
		if err != nil {
			return nil, err
		}
		_, compKeyParts, err := ctx.GetStub().SplitCompositeKey(resp.Key)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to split composite key: %s",
				err.Error())
		}
		rid := compKeyParts[1]
		results = append(results, rid)
	}
	if len(results) == 0 {
		return nil, fmt.Errorf(
			"No results found with such criteria. Check parameters: %q",
			params)
	}
	return results, nil
}

func (s *SmartContract) GetReportById(
	ctx contractapi.TransactionContextInterface) (*Report, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 1 && len(params) != 2 {
		return nil, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: ReportID [, public|private]")
	}
	rid := params[0]
	var repJSONAsBytes []byte
	var err error
	if len(params) == 1 {
		repJSONAsBytes, err = getDataHighestPermission(ctx.GetStub(), rid)
		if err != nil {
			return nil, err
		}
	} else {
		collect, err := getCollection(params[1])
		if err != nil {
			return nil, err
		}
		repJSONAsBytes, err = getData(ctx.GetStub(), rid, collect)
		if err != nil {
			return nil, err
		}
	}
	report := new(Report)
	err = json.Unmarshal(repJSONAsBytes, report)
	if err != nil {
		return nil, fmt.Errorf(
			"Failed to unmarshall JSON: %s",
			err.Error())
	}
	return report, nil
}

func (s *SmartContract) GetReportHashById(
	ctx contractapi.TransactionContextInterface) (string, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 1 && len(params) != 2 {
		return "", fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: ReportID [, public|private]")
	}
	rid := params[0]
	var hashAsBytes []byte
	var err error
	if len(params) == 1 {
		hashAsBytes, err = ctx.GetStub().GetPrivateDataHash(
			privateCollection, rid)
		if err != nil || hashAsBytes == nil {
			hashAsBytes, err = ctx.GetStub().GetPrivateDataHash(
				publicCollection, rid)
			if err != nil {
				return "", fmt.Errorf(
					"Failed to retrieve blockchain data hash: %s: %s",
					rid, err.Error())
			} else if hashAsBytes == nil {
				return "", fmt.Errorf(
					"No result found with such criteria: %s",
					rid)
			}
		}
	} else {
		collect, err := getCollection(params[1])
		if err != nil {
			return "", err
		}
		hashAsBytes, err = ctx.GetStub().GetPrivateDataHash(collect, rid)
		if err != nil {
			return "", fmt.Errorf(
				"Failed to retrieve blockchain data hash: %s: %s",
				rid, err.Error())
		} else if hashAsBytes == nil {
			return "", fmt.Errorf(
				"No result found with such criteria: %s",
				rid)
		}
	}
	return fmt.Sprintf("%x", string(hashAsBytes)), nil
}

func (s *SmartContract) GetReportsByOrganization(
	ctx contractapi.TransactionContextInterface) ([]Report, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 1 && len(params) != 2 {
		return nil, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: OrgName [, public|private]")
	}
	org := params[0]
	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexOrgRepId, []string {org},
		publicCollection, params)
	if err != nil {
		return nil, err
	}
	defer resIterator.Close()
	var repJSONAsBytes []byte
	results := []Report {}
	for resIterator.HasNext() {
		resp, err := resIterator.Next()
		if err != nil {
			return nil, err
		}
		_, compKeyParts, err := ctx.GetStub().SplitCompositeKey(resp.Key)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to split composite key: %s",
				err.Error())
		}
		rid := compKeyParts[1]
		if len(params) == 1 {
			repJSONAsBytes, err = getDataHighestPermission(ctx.GetStub(), rid)
			if err != nil {
				return nil, err
			}
		} else {
			collect, err := getCollection(params[1])
			if err != nil {
				return nil, err
			}
			repJSONAsBytes, err = getData(ctx.GetStub(), rid, collect)
			if err != nil {
				return nil, err
			}
		}
		report := new(Report)
		err = json.Unmarshal(repJSONAsBytes, report)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to unmarshall JSON: %s",
				err.Error())
		}
		results = append(results, *report)
	}
	if len(results) == 0 {
		return nil, fmt.Errorf(
			"No results found with such criteria. Check parameters: %q",
			params)
	}
	return results, nil
}

func (s *SmartContract) GetTotalReportsByOrganization(
	ctx contractapi.TransactionContextInterface) (int, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 1 {
		return -1, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: OrgName")
	}
	org := params[0]
	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexOrgRepId, []string {org},
		publicCollection, params)
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

func (s *SmartContract) GetReportsIdByOrganization(
	ctx contractapi.TransactionContextInterface) ([]string, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 1 {
		return nil, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: OrgName")
	}
	org := params[0]
	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexOrgRepId, []string {org},
		publicCollection, params)
	if err != nil {
		return nil, err
	}
	defer resIterator.Close()
	results := []string {}
	for resIterator.HasNext() {
		resp, err := resIterator.Next()
		if err != nil {
			return nil, err
		}
		_, compKeyParts, err := ctx.GetStub().SplitCompositeKey(resp.Key)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to split composite key: %s",
				err.Error())
		}
		rid := compKeyParts[1]
		results = append(results, rid)
	}
	if len(results) == 0 {
		return nil, fmt.Errorf(
			"No results found with such criteria. Check parameters: %q",
			params)
	}
	return results, nil
}

func (s *SmartContract) GetReportsByDate(
	ctx contractapi.TransactionContextInterface) ([]Report, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) < 1 || len(params) > 3 {
		return nil, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: YYYY-MM [, OrgName [, public|private]]")
	}
	date := params[0]
	var orgAsDB bool = false
	var partialKey = []string {date}
	if len(params) > 1 && params[1] != "private" && params[1] != "public" {
		org := params[1]
		partialKey = []string {date, org}
	} else if len(params) > 1 {
		orgAsDB = true
	}
	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexDateOrgRepId, partialKey,
		publicCollection, params)
	if err != nil {
		return nil, err
	}
	defer resIterator.Close()
	var repJSONAsBytes []byte
	results := []Report {}
	for resIterator.HasNext() {
		resp, err := resIterator.Next()
		if err != nil {
			return nil, err
		}
		_, compKeyParts, err := ctx.GetStub().SplitCompositeKey(resp.Key)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to split composite key: %s",
				err.Error())
		}
		rid := compKeyParts[2]
		if len(params) < 3 && !orgAsDB {
			repJSONAsBytes, err = getDataHighestPermission(ctx.GetStub(), rid)
			if err != nil {
				return nil, err
			}
		} else {
			var collect string
			if orgAsDB {
				collect, err = getCollection(params[1])
			} else {
				collect, err = getCollection(params[2])
			}
			if err != nil {
				return nil, err
			}
			repJSONAsBytes, err = getData(ctx.GetStub(), rid, collect)
			if err != nil {
				return nil, err
			}
		}
		report := new(Report)
		err = json.Unmarshal(repJSONAsBytes, report)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to unmarshall JSON: %s",
				err.Error())
		}
		results = append(results, *report)
	}
	if len(results) == 0 {
		return nil, fmt.Errorf(
			"No results found with such criteria. Check parameters: %q",
			params)
	}
	return results, nil
}

func (s *SmartContract) GetTotalReportsByDate(
	ctx contractapi.TransactionContextInterface) (int, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) != 1 && len(params) != 2 {
		return -1, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: YYYY-MM [, OrgName]")
	}
	date := params[0]
	var partialKey = []string {date}
	if len(params) > 1 {
		org := params[1]
		partialKey = []string {date, org}
	}
	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexDateOrgRepId, partialKey,
		publicCollection, params)
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

func (s *SmartContract) GetReportsIdByDate(
	ctx contractapi.TransactionContextInterface) ([]string, error) {

	_, params := ctx.GetStub().GetFunctionAndParameters()
	if len(params) < 1 || len(params) > 2 {
		return nil, fmt.Errorf(
			"Incorrect number of arguments. " +
				"Expecting: YYYY-MM [, OrgName]")
	}
	date := params[0]
	var partialKey = []string {date}
	if len(params) > 1 {
		org := params[1]
		partialKey = []string {date, org}
	}
	resIterator, err := getDataByPartialCompKey(
		ctx.GetStub(), indexDateOrgRepId, partialKey,
		publicCollection, params)
	if err != nil {
		return nil, err
	}
	defer resIterator.Close()
	results := []string {}
	for resIterator.HasNext() {
		resp, err := resIterator.Next()
		if err != nil {
			return nil, err
		}
		_, compKeyParts, err := ctx.GetStub().SplitCompositeKey(resp.Key)
		if err != nil {
			return nil, fmt.Errorf(
				"Failed to split composite key: %s",
				err.Error())
		}
		rid := compKeyParts[2]
		results = append(results, rid)
	}
	if len(results) == 0 {
		return nil, fmt.Errorf(
			"No results found with such criteria. Check parameters: %q",
			params)
	}
	return results, nil
}

func (s *SmartContract) Help(
	ctx contractapi.TransactionContextInterface) []SmartContractHelp {

	results := []SmartContractHelp {
		{"StoreReport",
			"Store report in blockchain",
			transStore, "none", "none"},
		{"DeleteReport",
			"Delete report from blockchain",
			transDelete, "none", "none"},
		{"GetReports",
			"Query all reports present in blockchain",
			"none", "none", "public|private"},
		{"GetTotalReports",
			"Query number of reports present in blockchain",
			"none", "none", "none"},
		{"GetReportsId",
			"Query all reports Id present in blockchain",
			"none", "none", "none"},
		{"GetReportById",
			"Query report information from a given Id",
			"none", "ReportID", "public|private"},
		{"GetReportHashById",
			"Query report data hash from a given Id",
			"none", "ReportID", "public|private"},
		{"GetReportsByOrganization",
			"Query all reports from a given Organization",
			"none", "OrgName", "public|private"},
		{"GetTotalReportsByOrganization",
			"Query number of reports from a given Organization",
			"none", "OrgName", "none"},
		{"GetReportsIdByOrganization",
			"Query all reports Id from a given Organization",
			"none", "none", "none"},
		{"GetReportsByDate",
			"Query all reports from a given Date and Organization",
			"none", "Date(YYYY-MM)", "OrgName, public|private"},
		{"GetTotalReportsByDate",
			"Query number of reports from a given Date and Organization",
			"none", "Date(YYYY-MM)", "OrgName, public|private"},
		{"GetReportsIdByDate",
			"Query all reports Id from a given Date and Organization",
			"none", "Date(YYYY-MM)", "OrgName, public|private"},
		{"Help",
			"Show smart contract available functions",
			"none", "none", "none"},
	}
	return results
}

func main() {
	chaincode, err := contractapi.NewChaincode(new(SmartContract))
	if err != nil {
		fmt.Printf("Error creating report chaincode: %s", err.Error())
		return
	}
	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting report chaincode: %s", err.Error())
	}
}
