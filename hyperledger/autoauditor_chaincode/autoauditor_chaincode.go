package main

import (
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric-chaincode-go/shim"
	"github.com/hyperledger/fabric-protos-go/peer"
)

// SimpleChaincode example simple Chaincode implementation
type SimpleChaincode struct {
}

type report struct {
	ObjectType   string `json:"docType"`
	Id           string `json:"id"`
	Organization string `json:"org"`
	Date         string `json:"date"`
	TotalVuln    int    `json:"nvuln"`
	AuditReport  string `json:"report"`
}

// ===================================================================================
// Main
// ===================================================================================
func main() {
	err := shim.Start(new(SimpleChaincode))
	if err != nil {
		fmt.Printf("Error starting Simple chaincode: %s", err)
	}
}

// Init initializes chaincode
// ===========================
func (t *SimpleChaincode) Init(stub shim.ChaincodeStubInterface) peer.Response {
	return shim.Success(nil)
}

// Invoke - Our entry point for Invocations
// ========================================
func (t *SimpleChaincode) Invoke(stub shim.ChaincodeStubInterface) peer.Response {
	function, args := stub.GetFunctionAndParameters()
	fmt.Println("invoke is running " + function)

	// Handle different functions
	switch function {
	case "new":
		//create a new report (simple)
		return t.newReport(stub, args)
	case "delete":
		//delete a report
		return t.deleteReport(stub, args)
	case "searchReport":
		//find report by Id
		return t.getById(stub, args)
	// case "searchByDate":
	// 	//find reports by date
	// 	return t.getByDate(stub, args)
	// case "searchByDateRange":
	// 	//find reports by date range
	// 	return t.getByDateRange(stub, args)
	// case "searchByOrganization":
	// 	//find reports by organization
	// 	return t.getByOrganization(stub, args)
	default:
		//error
		fmt.Println("invoke did not find func: " + function)
		return shim.Error(" invocation")
	}
}

// ============================================================
// newReport - create a new report, store into chaincode state
// ============================================================
func (t *SimpleChaincode) newReport(stub shim.ChaincodeStubInterface, args []string) peer.Response {
	var err error

	// ==== Input sanitation ====
	fmt.Println("- start newReport")

	if len(args) != 0 {
		return shim.Error("Incorrect number of arguments. Private report data must be passed in transient map.")
	}

	transMap, err := stub.GetTransient()
	if err != nil {
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
		Role         string `json:"role"`
		Organization string `json:"org"`
		Date         string `json:"date"`
		NVuln        int    `json: nvuln`
		Report       string `json:"report"`
	}

	var reportInput reportTransientInput
	err = json.Unmarshal(reportJsonBytes, &reportInput)
	if err != nil {
		return shim.Error("Failed to decode JSON of: " + string(reportJsonBytes))
	}

	if len(reportInput.Id) == 0 {
		return shim.Error("id field must be a non-empty string")
	}
	if len(reportInput.Organization) == 0 {
		return shim.Error("org field must be a non-empty string")
	}
	if len(reportInput.Date) == 0 {
		return shim.Error("date field must be a non-empty string")
	}
	if reportInput.NVuln <= 0 {
		return shim.Error("nvuln field must be a positive integer")
	}
	if len(reportInput.Report) == 0 {
		return shim.Error("report field must be a non-empty string")
	}

	collect := "collectAARep"
	objT := "AutoAuditorReport"
	switch reportInput.Role {
	case "simple":
		collect = collect + "S"
	case "medium":
		collect = collect + "M"
	case "full":
		collect = collect + "F"
	}

	reportId := reportInput.Id
	// ==== Check if report already exists ====
	reportAsBytes, err := stub.GetPrivateData(collect, reportId)
	if err != nil {
		return shim.Error("Failed to get report: " + err.Error())
	} else if reportAsBytes != nil {
		fmt.Println("This report already exists: " + reportId)
		return shim.Error("This report already exists: " + reportId)
	}

	// ==== Create report object, marshal to JSON, and save to state ====
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

	// === Save report to state ===
	err = stub.PutPrivateData(collect, reportInput.Id, reportJSONasBytes)
	if err != nil {
		return shim.Error(err.Error())
	}

	// ==== Report saved. Return success ====
	fmt.Println("- end create report")
	return shim.Success(nil)
}

// ===============================================
// getById find a report by Id from chaincode state
// ===============================================
func (t *SimpleChaincode) getById(stub shim.ChaincodeStubInterface, args []string) peer.Response {
	var id, jsonResp, role string
	var valAsbytes []byte
	var err error

	if len(args) < 1 || len(args) > 2 {
		return shim.Error("Incorrect number of arguments. Expecting id of the report to query (or level of report: simple, medium, full)")
	}

	id = args[0]

	if len(args) == 1 {
		valAsbytes, err = stub.GetPrivateData("collectAARepF", id) // try full report
		if err != nil || valAsbytes == nil {
			valAsbytes, err = stub.GetPrivateData("collectAARepM", id) // try medium report
			if err != nil || valAsbytes == nil {
				valAsbytes, err = stub.GetPrivateData("collectAARepS", id) // try simple report
				if err != nil {
					jsonResp = "{\"Error\":\"Failed to get report " + id + ": " + err.Error() + "\"}"
					return shim.Error(jsonResp)
				} else if valAsbytes == nil {
					jsonResp = "{\"Error\":\"Report does not exist: " + id + "\"}"
					return shim.Error(jsonResp)
				}
			}
		}
	} else {
		role = args[1]
		collect := "collectAARep"
		switch role {
		case "simple":
			collect = collect + "S"
		case "medium":
			collect = collect + "M"
		case "full":
			collect = collect + "F"
		}

		valAsbytes, err = stub.GetPrivateData(collect, id) // search in collection passed as argument
		if err != nil {
			jsonResp = "{\"Error\":\"Failed to get report " + id + ": " + err.Error() + "\"}"
			return shim.Error(jsonResp)
		} else if valAsbytes == nil {
			jsonResp = "{\"Error\":\"Report does not exist: " + id + "\"}"
			return shim.Error(jsonResp)
		}
	}

	return shim.Success(valAsbytes)
}

// ==================================================
// delete - remove a report key/value pair from state
// ==================================================
func (t *SimpleChaincode) deleteReport(stub shim.ChaincodeStubInterface, args []string) peer.Response {
	fmt.Println("- start delete report")

	type reportDeleteTransientInput struct {
		Id string `json:"id"`
	}

	if len(args) != 0 {
		return shim.Error("Incorrect number of arguments. Private report id must be passed in transient map.")
	}

	transMap, err := stub.GetTransient()
	if err != nil {
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
		return shim.Error("Failed to decode JSON of: " + string(reportDeleteJsonBytes))
	}

	if len(reportDeleteInput.Id) == 0 {
		return shim.Error("id field must be a non-empty string.")
	}

	// Delete all report details
	err = stub.DelPrivateData("collectAARepS", reportDeleteInput.Id)
	if err != nil {
		return shim.Error(err.Error())
	}

	err = stub.DelPrivateData("collectAARepM", reportDeleteInput.Id)
	if err != nil {
		return shim.Error(err.Error())
	}

	err = stub.DelPrivateData("collectAARepF", reportDeleteInput.Id)
	if err != nil {
		return shim.Error(err.Error())
	}

	return shim.Success(nil)
}
