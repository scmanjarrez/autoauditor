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

var publicCollection = "colAaRep"
var privateCollection = "colAaRepPriv"

type Report struct {
	ObjectType   string `json:"docType"`
	Id           string `json:"id"`
	Organization string `json:"org"`
	Date         string `json:"date"`
	TotalVuln    int    `json:"nvuln"`
	AuditReport  string `json:"report"`
}

func getCollection(collection string) (string, error) {
	switch collection {
	case "public":
		return publicCollection, nil
	case "private":
		return privateCollection, nil
	default:
		return "", fmt.Errorf("Collection does not exist: %s. Choose between public or private.", collection)
	}
}

func getDataHighestPermission(ctx contractapi.TransactionContextInterface, id string) ([]byte, error) {
	reportJSON, err := ctx.GetStub().GetPrivateData(privateCollection, id) // try private report
	if err != nil || reportJSON == nil {
		reportJSON, err = ctx.GetStub().GetPrivateData(publicCollection, id) // try simple report
		if err != nil {
			return nil, fmt.Errorf("Failed to get report %s: %s", id, err.Error())
		} else if reportJSON == nil {
			return nil, fmt.Errorf("Report does not exist: %s", id)
		}
	}
	return reportJSON, nil
}

func (s *SmartContract) NewReport(ctx contractapi.TransactionContextInterface) error {
	transMap, err := ctx.GetStub().GetTransient()
	if err != nil { // transient map, input data not stored in transaction record
		return fmt.Errorf("Failed to get transient: %s", err.Error())
	}

	transientReportJSON, ok := transMap["report"]
	if !ok {
		return fmt.Errorf("report not found in the transient map.")
	}

	if len(transientReportJSON) == 0 {
		return fmt.Errorf("report value in the transient map must be a non-empty JSON string.")
	}

	type reportTransientInput struct {
		Id           string `json:"id"`
		Organization string `json:"org"`
		Date         string `json:"date"`
		NVuln        int    `json:"nvuln"`
		Private      bool   `json:"private"`
		Report       string `json:"report"`
	}

	var reportInput reportTransientInput
	err = json.Unmarshal(transientReportJSON, &reportInput)
	if err != nil {
		return fmt.Errorf("Failed to unmarshall JSON: %s", err.Error())
	}

	if len(reportInput.Id) == 0 {
		return fmt.Errorf("id field must be a non-empty string.")
	}

	if len(reportInput.Organization) == 0 {
		return fmt.Errorf("org field must be a non-empty string.")
	}

	if len(reportInput.Date) == 0 {
		return fmt.Errorf("date field must be a non-empty string.")
	}

	if reportInput.NVuln <= 0 {
		return fmt.Errorf("nvuln field must be a positive integer.")
	}

	if len(reportInput.Report) == 0 {
		return fmt.Errorf("report field must be a non-empty string.")
	}

	collect := publicCollection

	if reportInput.Private {
		collect = privateCollection
	}

	objT := "AutoauditorReport"

	reportId := reportInput.Id

	reportJSON, err := ctx.GetStub().GetPrivateData(collect, reportId)
	if err != nil { // check in the ledger if reportId already exists
		return fmt.Errorf("Failed to get report %s: %s", reportId, err.Error())
	} else if reportJSON != nil {
		return fmt.Errorf("Report already exists: %s", reportId)
	}

	report := &Report{
		ObjectType:   objT,
		Id:           reportInput.Id,
		Organization: reportInput.Organization,
		Date:         reportInput.Date,
		TotalVuln:    reportInput.NVuln,
		AuditReport:  reportInput.Report,
	}

	reportJSONasBytes, err := json.Marshal(report)
	if err != nil {
		return fmt.Errorf("Failed to marshall report: %s", err.Error())
	}

	err = ctx.GetStub().PutPrivateData(collect, reportInput.Id, reportJSONasBytes)
	if err != nil {
		return fmt.Errorf("Failed to store report %s: %s", reportInput.Id, err.Error())
	}

	if collect == publicCollection { // save a composite key to query all reports of organization
		indexName := "organization~id"
		organizationIdIndexKey, err := ctx.GetStub().CreateCompositeKey(indexName, []string{reportInput.Organization, reportInput.Id})
		if err != nil {
			return fmt.Errorf("Failed to generate composite key %s: %s", organizationIdIndexKey, err.Error())
		}
		value := []byte{0x00} // passing a 'nil' value will effectively delete the key from state, therefore we pass null character as value
		err = ctx.GetStub().PutPrivateData(collect, organizationIdIndexKey, value)
		if err != nil {
			return fmt.Errorf("Failed to store composite key %s: %s", organizationIdIndexKey, err.Error())
		}

		indexName = "date~organization~id"
		date := reportInput.Date[:7]
		organizationIdIndexKey, err = ctx.GetStub().CreateCompositeKey(indexName, []string{date, reportInput.Organization, reportInput.Id})
		if err != nil {
			return fmt.Errorf("Failed to generate composite key %s: %s", organizationIdIndexKey, err.Error())
		}
		value = []byte{0x00} // passing a 'nil' value will effectively delete the key from state, therefore we pass null character as value
		err = ctx.GetStub().PutPrivateData(collect, organizationIdIndexKey, value)
		if err != nil {
			return fmt.Errorf("Failed to store composite key %s: %s", organizationIdIndexKey, err.Error())
		}
	}

	return nil
}

func (s *SmartContract) DeleteReport(ctx contractapi.TransactionContextInterface) error {

	transMap, err := ctx.GetStub().GetTransient()
	if err != nil { // transient map, input data not stored in transaction record
		return fmt.Errorf("Failed to get transient: %s", err.Error())
	}

	transientDeleteReportJSON, ok := transMap["report_delete"]
	if !ok {
		return fmt.Errorf("report_delete not found in the transient map.")
	}

	if len(transientDeleteReportJSON) == 0 {
		return fmt.Errorf("report_delete value in the transient map must be a non-empty JSON string.")
	}

	type reportDelete struct {
		Id string `json:"id"`
	}

	var reportDeleteInput reportDelete
	err = json.Unmarshal(transientDeleteReportJSON, &reportDeleteInput)
	if err != nil {
		return fmt.Errorf("Failed to unmarshall JSON: %s", err.Error())
	}

	if len(reportDeleteInput.Id) == 0 {
		return fmt.Errorf("id field must be a non-empty string.")
	}

	reportJSON, err := ctx.GetStub().GetPrivateData(publicCollection, reportDeleteInput.Id)
	if err != nil { // we need to query the report from chaincode state to obtain the organization info
		return fmt.Errorf("Failed to get report %s: %s", reportDeleteInput.Id, err.Error())
	} else if reportJSON == nil {
		return fmt.Errorf("Report does not exists: %s", reportDeleteInput.Id)
	}

	var reportToDelete Report
	err = json.Unmarshal([]byte(reportJSON), &reportToDelete)
	if err != nil {
		return fmt.Errorf("Failed to unmarshall JSON: %s", err.Error())
	}

	indexName := "organization~id"
	organizationIdIndexKey, err := ctx.GetStub().CreateCompositeKey(indexName, []string{reportToDelete.Organization, reportToDelete.Id})
	if err != nil {
		return fmt.Errorf("Failed to generate composite key (deletion) %s: %s", organizationIdIndexKey, err.Error())
	}
	err = ctx.GetStub().DelPrivateData(publicCollection, organizationIdIndexKey)
	if err != nil {
		return fmt.Errorf("Failed to delete composite key %s: %s", organizationIdIndexKey, err.Error())
	}

	indexName = "date-organization~id"
	date := reportToDelete.Date[:7]
	organizationIdIndexKey, err = ctx.GetStub().CreateCompositeKey(indexName, []string{date, reportToDelete.Organization, reportToDelete.Id})
	if err != nil {
		return fmt.Errorf("Failed to generate composite key (deletion) %s: %s", organizationIdIndexKey, err.Error())
	}
	err = ctx.GetStub().DelPrivateData(publicCollection, organizationIdIndexKey)
	if err != nil {
		return fmt.Errorf("Failed to delete composite key %s: %s", organizationIdIndexKey, err.Error())
	}

	err = ctx.GetStub().DelPrivateData(publicCollection, reportDeleteInput.Id)
	if err != nil { // delete from public collection
		return fmt.Errorf("Failed to delete public report %s: %s", reportDeleteInput.Id, err.Error())
	}

	err = ctx.GetStub().DelPrivateData(privateCollection, reportDeleteInput.Id)
	if err != nil { // delete from private collection
		return fmt.Errorf("Failed to delete private report %s: %s", reportDeleteInput.Id, err.Error())
	}

	return nil
}

func (s *SmartContract) GetReportById(ctx contractapi.TransactionContextInterface) (*Report, error) {
	_, params := ctx.GetStub().GetFunctionAndParameters()

	var reportJSON []byte
	var err error

	if len(params) < 1 || len(params) > 2 {
		return nil, fmt.Errorf("Incorrect number of arguments. Expecting: ReportID [, public|private].")
	}

	id := params[0]

	if len(params) == 1 { // if no collection given, client will receive the higher report according to its permissions
		reportJSON, err = getDataHighestPermission(ctx, id)
		if err != nil {
			return nil, fmt.Errorf("Failed to get report %s: %s", id, err.Error())
		}
	} else {
		collect, err := getCollection(params[1])
		if err != nil {
			return nil, err
		}

		reportJSON, err = ctx.GetStub().GetPrivateData(collect, id)
		if err != nil {
			return nil, fmt.Errorf("Failed to get report %s: %s", id, err.Error())
		} else if reportJSON == nil {
			return nil, fmt.Errorf("Report does not exist: %s", id)
		}
	}

	report := new(Report)
	err = json.Unmarshal(reportJSON, report)
	if err != nil {
		return nil, fmt.Errorf("Failed to unmarshall JSON: %s", err.Error())
	}

	return report, nil
}

func (s *SmartContract) GetReportHash(ctx contractapi.TransactionContextInterface) (string, error) {
	_, params := ctx.GetStub().GetFunctionAndParameters()

	var hashAsBytes []byte
	var err error

	if len(params) < 1 || len(params) > 2 {
		return "", fmt.Errorf("Incorrect number of arguments. Expecting: ReportID [, public|private].")
	}

	id := params[0]

	if len(params) == 1 { // if no collection given, client will receive the higher report according to its permissions
		hashAsBytes, err = ctx.GetStub().GetPrivateDataHash(privateCollection, id) // try private report
		if err != nil || hashAsBytes == nil {
			hashAsBytes, err = ctx.GetStub().GetPrivateDataHash(publicCollection, id) // try simple report
			if err != nil {
				return "", fmt.Errorf("Failed to get report hash for report %s: %s", id, err.Error())
			} else if hashAsBytes == nil {
				return "", fmt.Errorf("Report does not exist: %s", id)
			}
		}
	} else {
		collect, err := getCollection(params[1])
		if err != nil {
			return "", err
		}
		hashAsBytes, err = ctx.GetStub().GetPrivateDataHash(collect, id)
		if err != nil {
			return "", fmt.Errorf("Failed to get %s data hash for report %s: %s", params[1], id, err.Error())
		} else if hashAsBytes == nil {
			return "", fmt.Errorf("Report does not exist: %s", id)
		}
	}

	return fmt.Sprintf("%x", string(hashAsBytes)), nil
}

func (s *SmartContract) GetReportsByOrganization(ctx contractapi.TransactionContextInterface) ([]Report, error) {
	_, params := ctx.GetStub().GetFunctionAndParameters()

	var reportJSON []byte
	var err error
	if len(params) < 1 || len(params) > 2 {
		return nil, fmt.Errorf("Incorrect number of arguments. Expecting: OrgName [, public|private].")
	}

	org := params[0]

	indexName := "organization~id"

	resultsIterator, err := ctx.GetStub().GetPrivateDataByPartialCompositeKey(publicCollection, indexName, []string{org})

	if err != nil {
		return nil, fmt.Errorf("Failed to get organization reports: %s", err.Error())
	} else if resultsIterator == nil {
		return nil, fmt.Errorf("Organization reports do not exist: %s", err.Error())
	}

	defer resultsIterator.Close()

	results := []Report{}

	for resultsIterator.HasNext() {
		response, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		_, compositeKeyParts, err := ctx.GetStub().SplitCompositeKey(response.Key)
		if err != nil {
			return nil, fmt.Errorf("Failed to split composite key: %s", err.Error())
		}

		id := compositeKeyParts[1]

		if len(params) == 1 { // if no collection given, client will receive the higher report according to its permissions
			reportJSON, err = getDataHighestPermission(ctx, id)
			if err != nil {
				return nil, fmt.Errorf("Failed to get report %s: %s", id, err.Error())
			}
		} else {
			collect, err := getCollection(params[1])
			if err != nil {
				return nil, err
			}

			reportJSON, err = ctx.GetStub().GetPrivateData(collect, id)
			if err != nil {
				return nil, fmt.Errorf("Failed to get report %s: %s", id, err.Error())
			} else if reportJSON == nil {
				return nil, fmt.Errorf("Report does not exist: %s", id)
			}
		}

		report := new(Report)
		err = json.Unmarshal(reportJSON, report)
		if err != nil {
			return nil, fmt.Errorf("Failed to unmarshall JSON: %s", err.Error())
		}

		results = append(results, *report)
	}

	return results, nil
}

func (s *SmartContract) GetTotalReportsByOrganization(ctx contractapi.TransactionContextInterface) (int, error) {
	_, params := ctx.GetStub().GetFunctionAndParameters()

	var err error
	if len(params) != 1 {
		return -1, fmt.Errorf("Incorrect number of arguments. Expecting: OrgName.")
	}

	org := params[0]

	indexName := "organization~id"

	resultsIterator, err := ctx.GetStub().GetPrivateDataByPartialCompositeKey(publicCollection, indexName, []string{org})

	if err != nil {
		return -1, fmt.Errorf("Failed to get organization reports: %s", err.Error())
	} else if resultsIterator == nil {
		return -1, fmt.Errorf("Organization reports do not exist: %s", err.Error())
	}

	defer resultsIterator.Close()

	total := 0

	for resultsIterator.HasNext() {
		_, err := resultsIterator.Next()
		if err != nil {
			return -1, err
		}

		total++
	}

	return total, nil
}

func (s *SmartContract) GetReportsIdByOrganization(ctx contractapi.TransactionContextInterface) ([]string, error) {
	_, params := ctx.GetStub().GetFunctionAndParameters()

	var err error
	if len(params) != 1 {
		return nil, fmt.Errorf("Incorrect number of arguments. Expecting: OrgName.")
	}

	org := params[0]

	indexName := "organization~id"

	resultsIterator, err := ctx.GetStub().GetPrivateDataByPartialCompositeKey(publicCollection, indexName, []string{org})

	if err != nil {
		return nil, fmt.Errorf("Failed to get organization reports: %s", err.Error())
	} else if resultsIterator == nil {
		return nil, fmt.Errorf("Organization reports do not exist: %s", err.Error())
	}

	defer resultsIterator.Close()

	results := []string{}

	for resultsIterator.HasNext() {
		response, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		_, compositeKeyParts, err := ctx.GetStub().SplitCompositeKey(response.Key)
		if err != nil {
			return nil, fmt.Errorf("Failed to split composite key: %s", err.Error())
		}

		id := compositeKeyParts[1]

		results = append(results, id)
	}

	return results, nil
}

func (s *SmartContract) GetReportsByDate(ctx contractapi.TransactionContextInterface) ([]Report, error) {
	_, params := ctx.GetStub().GetFunctionAndParameters()

	var reportJSON []byte
	var err error
	var orgAsDB bool = false

	if len(params) < 1 || len(params) > 3 {
		return nil, fmt.Errorf("Incorrect number of arguments. Expecting: YYYY-MM [, OrgName [, public|private]].")
	}

	date := params[0]

	var resultsIterator shim.StateQueryIteratorInterface
	indexName := "date~organization~id"
	if len(params) > 1 && params[1] != "private" && params[1] != "public" {
		org := params[1]
		resultsIterator, err = ctx.GetStub().GetPrivateDataByPartialCompositeKey(publicCollection, indexName, []string{date, org})
	} else {
		resultsIterator, err = ctx.GetStub().GetPrivateDataByPartialCompositeKey(publicCollection, indexName, []string{date})
		if len(params) > 1 {
			orgAsDB = true
		}
	}

	if err != nil {
		return nil, fmt.Errorf("Failed to get reports by date: %s", err.Error())
	} else if resultsIterator == nil {
		return nil, fmt.Errorf("Date reports do not exist: %s", err.Error())
	}

	defer resultsIterator.Close()

	results := []Report{}

	for resultsIterator.HasNext() {
		response, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		_, compositeKeyParts, err := ctx.GetStub().SplitCompositeKey(response.Key)
		if err != nil {
			return nil, fmt.Errorf("Failed to split composite key: %s", err.Error())
		}

		id := compositeKeyParts[2]

		if len(params) < 3 && !orgAsDB { // if no collection given, client will receive the higher report according to its permissions
			reportJSON, err = getDataHighestPermission(ctx, id)
			if err != nil {
				return nil, fmt.Errorf("Failed to get report %s: %s", id, err.Error())
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

			reportJSON, err = ctx.GetStub().GetPrivateData(collect, id)
			if err != nil {
				return nil, fmt.Errorf("Failed to get report %s: %s", id, err.Error())
			} else if reportJSON == nil {
				return nil, fmt.Errorf("Report does not exist: %s", id)
			}
		}

		report := new(Report)
		err = json.Unmarshal(reportJSON, report)
		if err != nil {
			return nil, fmt.Errorf("Failed to unmarshall JSON: %s", err.Error())
		}

		results = append(results, *report)
	}

	if len(results) == 0 {
		return nil, fmt.Errorf("No results found for such criteria. Check parameters: %+q", params)
	}
	return results, nil
}

func (s *SmartContract) GetTotalReportsByDate(ctx contractapi.TransactionContextInterface) (int, error) {
	_, params := ctx.GetStub().GetFunctionAndParameters()

	var err error

	if len(params) < 1 || len(params) > 2 {
		return -1, fmt.Errorf("Incorrect number of arguments. Expecting: YYYY-MM [, OrgName].")
	}

	date := params[0]

	var resultsIterator shim.StateQueryIteratorInterface
	indexName := "date~organization~id"
	if len(params) > 1 && params[1] != "private" && params[1] != "public" {
		org := params[1]
		resultsIterator, err = ctx.GetStub().GetPrivateDataByPartialCompositeKey(publicCollection, indexName, []string{date, org})
	} else {
		resultsIterator, err = ctx.GetStub().GetPrivateDataByPartialCompositeKey(publicCollection, indexName, []string{date})
	}

	if err != nil {
		return -1, fmt.Errorf("Failed to get reports by date: %s", err.Error())
	} else if resultsIterator == nil {
		return -1, fmt.Errorf("Date reports do not exist: %s", err.Error())
	}

	defer resultsIterator.Close()

	total := 0
	for resultsIterator.HasNext() {
		_, err := resultsIterator.Next()
		if err != nil {
			return -1, err
		}
		total++
	}

	if total == 0 {
		return -1, fmt.Errorf("No results found for such criteria. Check parameters: %+q", params)
	}
	return total, nil
}

func (s *SmartContract) GetReportsIdByDate(ctx contractapi.TransactionContextInterface) ([]string, error) {
	_, params := ctx.GetStub().GetFunctionAndParameters()

	var err error

	if len(params) < 1 || len(params) > 2 {
		return nil, fmt.Errorf("Incorrect number of arguments. Expecting: YYYY-MM [, OrgName].")
	}

	date := params[0]

	var resultsIterator shim.StateQueryIteratorInterface
	indexName := "date~organization~id"
	if len(params) > 1 && params[1] != "private" && params[1] != "public" {
		org := params[1]
		resultsIterator, err = ctx.GetStub().GetPrivateDataByPartialCompositeKey(publicCollection, indexName, []string{date, org})
	} else {
		resultsIterator, err = ctx.GetStub().GetPrivateDataByPartialCompositeKey(publicCollection, indexName, []string{date})
	}

	if err != nil {
		return nil, fmt.Errorf("Failed to get reports by date: %s", err.Error())
	} else if resultsIterator == nil {
		return nil, fmt.Errorf("Date reports do not exist: %s", err.Error())
	}

	defer resultsIterator.Close()

	results := []string{}

	for resultsIterator.HasNext() {
		response, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		_, compositeKeyParts, err := ctx.GetStub().SplitCompositeKey(response.Key)
		if err != nil {
			return nil, fmt.Errorf("Failed to split composite key: %s", err.Error())
		}

		id := compositeKeyParts[2]

		results = append(results, id)
	}

	if len(results) == 0 {
		return nil, fmt.Errorf("No results found for such criteria. Check parameters: %+q", params)
	}
	return results, nil
}

type smartContractFuntion struct {
	Name         string `json:"name"`
	Description  string `json:"description"`
	TransientMap string `json:"transient"`
	Arg          string `json:"arg"`
	OptArg       string `json:"optarg"`
}

func (s *SmartContract) Help(ctx contractapi.TransactionContextInterface) []smartContractFuntion {
	results := []smartContractFuntion{
		{"NewReport", "Store report in the ledger", "report", "", ""},
		{"DeleteReport", "Delete report from the ledger", "report_delete", "", ""},
		{"GetReportById", "Query report information given an ID", "", "ReportID", "public|private"},
		{"GetReportHash", "Query report data hash given an ID", "", "ReportID", "public|private"},
		{"GetReportsByOrganization", "Query all reports information based on organization", "", "OrgName", "public|private"},
		{"GetReportsByDate", "Query all reports information based on date and organization", "", "Date(YYYY-MM)", "OrgaName, public|private"},
		{"Help", "Show Smart Contract available functions", "", "", ""}}
	return results
}

func main() {

	chaincode, err := contractapi.NewChaincode(new(SmartContract))

	if err != nil {
		fmt.Printf("Error creating autoauditor chaincode: %s", err.Error())
		return
	}

	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting autoauditor chaincode: %s", err.Error())
	}
}
