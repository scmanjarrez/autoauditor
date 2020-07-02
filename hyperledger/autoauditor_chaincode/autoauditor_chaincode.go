package main

import (
	"bytes"
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric-chaincode-go/shim"
	"github.com/hyperledger/fabric-protos-go/peer"
)

type SimpleChaincode struct {
}

var pubcol string = "colAaRep"
var privcol string = "colAaRepPriv"

type report struct {
	ObjectType   string `json:"docType"`
	Id           string `json:"id"`
	Organization string `json:"org"`
	Date         string `json:"date"`
	TotalVuln    int    `json:"nvuln"`
	AuditReport  string `json:"report"`
}

func main() {
	err := shim.Start(new(SimpleChaincode))
	if err != nil {
		fmt.Printf("Error starting Simple chaincode: %s", err)
	}
}

func (t *SimpleChaincode) Init(stub shim.ChaincodeStubInterface) peer.Response {
	return shim.Success(nil)
}

func (t *SimpleChaincode) Invoke(stub shim.ChaincodeStubInterface) peer.Response {
	function, args := stub.GetFunctionAndParameters()

	switch function {
	case "new":
		return t.newReport(stub, args)
	case "delete":
		return t.deleteReport(stub, args)
	case "getReport":
		return t.getReportById(stub, args)
	case "getReportHash":
		return t.getReportHash(stub, args)
	// case "searchByDate":
	// 	//find reports by date
	// 	return t.getByDate(stub, args)
	// case "searchByDateRange":
	// 	//find reports by date range
	// 	return t.getByDateRange(stub, args)
	case "getOrganizationReports":
		//find reports by organization
		return t.getReportsByOrganization(stub, args)
	default:
		return shim.Error("Invoke function not found. Choose between new, delete, getReport, getReportHash and getOrganizationReports.")
	}
}

func (t *SimpleChaincode) newReport(stub shim.ChaincodeStubInterface, args []string) peer.Response {
	var err error

	if len(args) != 0 {
		return shim.Error("Incorrect number of arguments. Private report data must be passed in transient map.")
	}

	transMap, err := stub.GetTransient()
	if err != nil { // transient map, input data not stored in transaction record
		return shim.Error("Error getting transient: " + err.Error())
	}

	reportJsonBytes, ok := transMap["aareport"]
	if !ok {
		return shim.Error("aareport must be a key in the transient map")
	}

	if len(reportJsonBytes) == 0 {
		return shim.Error("aareport value in the transient map must be a non-empty JSON string")
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
	err = json.Unmarshal(reportJsonBytes, &reportInput)
	if err != nil {
		return shim.Error("Failed to decode JSON of: " + string(reportJsonBytes))
	}

	if len(reportInput.Id) == 0 {
		return shim.Error("id field must be a non-empty string.")
	}

	if len(reportInput.Organization) == 0 {
		return shim.Error("org field must be a non-empty string.")
	}

	if len(reportInput.Date) == 0 {
		return shim.Error("date field must be a non-empty string.")
	}

	if reportInput.NVuln <= 0 {
		return shim.Error("nvuln field must be a positive integer.")
	}

	if len(reportInput.Report) == 0 {
		return shim.Error("report field must be a non-empty string.")
	}

	var collect string

	if reportInput.Private {
		collect = privcol
	} else {
		collect = pubcol
	}

	objT := "AutoauditorReport"

	reportId := reportInput.Id

	reportAsBytes, err := stub.GetPrivateData(collect, reportId)
	if err != nil { // check in the ledger if reportId already exists
		return shim.Error("Failed to get report " + reportId + ": " + err.Error())
	} else if reportAsBytes != nil {
		return shim.Error("Report already exists: " + reportId)
	}

	report := &report{
		ObjectType:   objT,
		Id:           reportInput.Id,
		Organization: reportInput.Organization,
		Date:         reportInput.Date,
		TotalVuln:    reportInput.NVuln,
		AuditReport:  reportInput.Report,
	}

	reportJSONasBytes, err := json.Marshal(report)
	if err != nil {
		return shim.Error(err.Error())
	}

	err = stub.PutPrivateData(collect, reportInput.Id, reportJSONasBytes)
	if err != nil {
		return shim.Error("Failed storing report " + reportInput.Id + ": " + err.Error())
	}

	if collect == pubcol { // save a composite key to query all reports of organization
		indexName := "organization~id"
		organizationIdIndexKey, err := stub.CreateCompositeKey(indexName, []string{reportInput.Organization, reportInput.Id})
		if err != nil {
			return shim.Error("Failed to generate composite key " + organizationIdIndexKey + ": " + err.Error())
		}
		value := []byte{0x00} // passing a 'nil' value will effectively delete the key from state, therefore we pass null character as value
		err = stub.PutPrivateData(collect, organizationIdIndexKey, value)
		if err != nil {
			return shim.Error("Failed storing composite key " + organizationIdIndexKey + ": " + err.Error())
		}
	}

	return shim.Success(nil)
}

func (t *SimpleChaincode) deleteReport(stub shim.ChaincodeStubInterface, args []string) peer.Response {
	type reportDeleteTransientInput struct {
		Id string `json:"id"`
	}

	if len(args) != 0 {
		return shim.Error("Incorrect number of arguments. Report id must be passed in transient map.")
	}

	transMap, err := stub.GetTransient()
	if err != nil { // transient map, input data not stored in transaction record
		return shim.Error("Error getting transient: " + err.Error())
	}

	reportDeleteJsonBytes, ok := transMap["aareport_delete"]
	if !ok {
		return shim.Error("aareport_delete must be a key in the transient map.")
	}

	if len(reportDeleteJsonBytes) == 0 {
		return shim.Error("aareport_delete value in the transient map must be a non-empty JSON string.")
	}

	var reportDeleteInput reportDeleteTransientInput
	err = json.Unmarshal(reportDeleteJsonBytes, &reportDeleteInput)
	if err != nil {
		return shim.Error("Failed to decode JSON: " + string(reportDeleteJsonBytes))
	}

	if len(reportDeleteInput.Id) == 0 {
		return shim.Error("id field must be a non-empty string.")
	}

	err = stub.DelPrivateData(pubcol, reportDeleteInput.Id)
	if err != nil { // delete from public collection
		return shim.Error("Failed deleting public report " + reportDeleteInput.Id + ": " + err.Error())
	}

	err = stub.DelPrivateData(privcol, reportDeleteInput.Id)
	if err != nil { // delete from private collection
		return shim.Error("Failed deleting private report " + reportDeleteInput.Id + ": " + err.Error())
	}

	reportAsBytes, err := stub.GetPrivateData(pubcol, reportDeleteInput.Id)
	if err != nil { // we need to query the report from chaincode state to obtain the organization info
		return shim.Error("Failed to get report " + reportDeleteInput.Id + ": " + err.Error())
	} else if reportAsBytes == nil {
		return shim.Error("Report does not exists: " + reportDeleteInput.Id)
	}

	var reportToDelete report
	err = json.Unmarshal([]byte(reportAsBytes), &reportToDelete)
	if err != nil {
		return shim.Error("Failed to decode JSON of: " + string(reportAsBytes))
	}

	indexName := "organization~id"
	organizationIdIndexKey, err := stub.CreateCompositeKey(indexName, []string{reportToDelete.Organization, reportToDelete.Id})
	if err != nil {
		return shim.Error("Failed to generate composite key (deletion) " + organizationIdIndexKey + ": " + err.Error())
	}
	err = stub.DelPrivateData(pubcol, organizationIdIndexKey)
	if err != nil {
		return shim.Error("Failed deleting composite key " + organizationIdIndexKey + ": " + err.Error())
	}

	return shim.Success(nil)
}

func (t *SimpleChaincode) getReportById(stub shim.ChaincodeStubInterface, args []string) peer.Response {
	var id string
	var reportAsBytes []byte
	var err error

	if len(args) < 1 || len(args) > 2 {
		return shim.Error("Incorrect number of arguments. Expecting id of the report to query. Optionally, database can be passed: public or private.")
	}

	id = args[0]

	if len(args) == 1 { // with no arguments, client will receive the higher report according to its permissions
		reportAsBytes, err = stub.GetPrivateData(privcol, id) // try private report
		if err != nil || reportAsBytes == nil {
			reportAsBytes, err = stub.GetPrivateData(pubcol, id) // try simple report
			if err != nil {
				return shim.Error("Failed to get report " + id + ": " + err.Error())
			} else if reportAsBytes == nil {
				return shim.Error("Report does not exist: " + id)
			}
		}
	} else {
		col := args[1]
		var collect string
		switch col {
		case "private":
			collect = privcol
		case "public":
			collect = pubcol
		default:
			return shim.Error("Collection does not exist: " + col + ". Choose between public or private")
		}

		reportAsBytes, err = stub.GetPrivateData(collect, id)
		if err != nil {
			return shim.Error("Failed to get report " + id + ": " + err.Error())
		} else if reportAsBytes == nil {
			return shim.Error("Report does not exist: " + id)
		}
	}

	return shim.Success(reportAsBytes)
}

func (t *SimpleChaincode) getReportHash(stub shim.ChaincodeStubInterface, args []string) peer.Response {
	var id string
	var err error
	var hashAsBytes []byte

	if len(args) < 1 || len(args) > 2 {
		return shim.Error("Incorrect number of arguments. Expecting id of the report to query. Optionally, database can be passed: public or private.")
	}

	id = args[0]

	if len(args) == 1 {
		hashAsBytes, err = stub.GetPrivateDataHash(privcol, id) // try private report
		if err != nil || hashAsBytes == nil {
			hashAsBytes, err = stub.GetPrivateDataHash(pubcol, id) // try simple report
			if err != nil {
				return shim.Error("Failed to get public data hash for report " + id + ": " + err.Error())
			} else if hashAsBytes == nil {
				return shim.Error("Report does not exist: " + id)
			}
		}
	} else {
		col := args[1]
		var collect string
		switch col {
		case "private":
			collect = privcol
		case "public":
			collect = pubcol
		default:
			return shim.Error("Collection does not exist: " + col + ". Choose between public or private")
		}

		hashAsBytes, err = stub.GetPrivateDataHash(collect, id)
		if err != nil {
			return shim.Error("Failed to get " + col + " data hash for report " + id + ": " + err.Error())
		} else if hashAsBytes == nil {
			return shim.Error("Report does not exist: " + id)
		}
	}

	return shim.Success(hashAsBytes)
}

func (t *SimpleChaincode) getReportsByOrganization(stub shim.ChaincodeStubInterface, args []string) peer.Response {
	var org string
	var reportAsBytes []byte
	var resultsIterator shim.StateQueryIteratorInterface
	var err error

	if len(args) < 1 || len(args) > 2 {
		return shim.Error("Incorrect number of arguments. Expecting organization name to query. Optionally, database can be passed: public or private.")
	}

	org = args[0]

	indexName := "organization~id"

	resultsIterator, err = stub.GetPrivateDataByPartialCompositeKey(pubcol, indexName, []string{org})
	if err != nil {
		return shim.Error("Failed to get organization reports: " + err.Error())
	} else if resultsIterator == nil {
		return shim.Error("Organization reports do not exist: " + err.Error())
	}
	defer resultsIterator.Close()

	// buffer is a JSON array containing QueryResults
	var buffer bytes.Buffer
	buffer.WriteString("[")

	bArrayMemberAlreadyWritten := false
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return shim.Error(err.Error())
		}
		_, compositeKeyParts, err := stub.SplitCompositeKey(queryResponse.Key)
		if err != nil {
			return shim.Error(err.Error())
		}
		returnedReportId := compositeKeyParts[1]

		if len(args) == 1 {
			reportAsBytes, err = stub.GetPrivateData(privcol, returnedReportId) // try private report
			if err != nil || reportAsBytes == nil {
				reportAsBytes, err = stub.GetPrivateData(pubcol, returnedReportId) // try simple report
				if err != nil {
					return shim.Error("Failed to get report " + returnedReportId + ": " + err.Error())
				} else if reportAsBytes == nil {
					return shim.Error("Report does not exist: " + returnedReportId)
				}
			}
		} else {
			col := args[1]
			var collect string
			switch col {
			case "private":
				collect = privcol
			case "public":
				collect = pubcol
			default:
				return shim.Error("Collection does not exist: " + col + ". Choose between public or private")
			}
			returnedReportId := compositeKeyParts[1]
			reportAsBytes, err = stub.GetPrivateData(collect, returnedReportId)
			if err != nil {
				return shim.Error("Failed to get report " + returnedReportId + ": " + err.Error())
			} else if reportAsBytes == nil {
				return shim.Error("Report does not exist: " + returnedReportId)
			}
		}

		// Add a comma before array members, suppress it for the first array member
		if bArrayMemberAlreadyWritten {
			buffer.WriteString(",")
		}

		buffer.WriteString(
			fmt.Sprintf(
				`{"ReportID": "%s", "ReportData": %s}`,
				returnedReportId, reportAsBytes,
			),
		)
		bArrayMemberAlreadyWritten = true
	}
	buffer.WriteString("]")

	return shim.Success(buffer.Bytes())
}
