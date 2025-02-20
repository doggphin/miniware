from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .fc.slides import (PhotoFinalCheckQuery, PhotoMediaType)
from sheets.sheets_requests import (SheetsRequest, SheetsResponse, RangeRequest)
from sheets.exceptions import (
    CustomException,
    UnknownException,
    MultiGroupCustomException,
    MultiGroupUnknownException
)

from sheets.photo_row import PhotoRow

@api_view(['GET'])
def fc_photo(request,
client_first_name : str,
client_last_name : str,
formatted_project_name : str,
dpi : int,
photo_type : str):
    count_reg = request.GET.get("count_reg", 0)
    count_hs = request.GET.get("count_hs", 0)
    count_oshs = request.GET.get("count_oshs", 0)
    group_number = request.GET.get("group_number")
    custom_group_name = request.GET.get("custom_group_name")

    slides_final_checker = PhotoFinalCheckQuery(
        client_first_name = client_first_name,
        client_last_name = client_last_name,
        formatted_project_name = formatted_project_name,

        group_identifier = group_number,
        custom_group_name = custom_group_name,
        is_corrected = "is_corrected" in request.GET,

        dpi = int(dpi),
        count_reg = int(count_reg),
        count_hs = int(count_hs),
        count_oshs = int(count_oshs),
        media_type = PhotoMediaType(photo_type)
    )

    try:
        slides_final_checker.final_check()
        return Response(data={"message" : "All good!"})
    except Exception as e:
        return Response(data={"message" : str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)


@api_view(['GET'])
def client_info(request, spreadsheet_id : str):
    ranges = [
        RangeRequest("Customer Info", "E6", "F6", 2)
        # gen_sheets_range("Customer Info", "E5", "E5"),
        # gen_sheets_range("Customer Info", "E6", "F6"),
    ]

    request = SheetsRequest(spreadsheet_id, ranges, True)
    response = request.execute()

    if(response.response_code != 200):
        return response.make_drf_response()

    return Response(data={"message" : {
        "title" : response.title,
        "client_first_name" : response.values[0][0],
        "client_last_name" : response.values[0][1]
    }})

    
    # client_data = get_batched_spreadsheet_ranges(spreadsheet_id, ranges)
    #client_data_range = gen_sheets_range("Customer Info", "E6", "F6")
    #client_data = get_single_spreadsheet_range(spreadsheet_id, client_data_range)
    # title = get_spreadsheet_title(spreadsheet_id)


@api_view(['GET'])
def photo_has_corrected(request, spreadsheet_id : str):
    is_corrected_column = gen_sheets_range("Photo Trns", "D", "D")
    corrected_column = get_single_spreadsheet_range(spreadsheet_id, is_corrected_column)

    has_corrected = False
    for value in corrected_column:
        if value == "Y":
            has_corrected = True
            break

    
    return Response(data={"message" : {
        "has_corrected_items" : has_corrected
    }})


@api_view(['GET'])
def photo_info_normal_row(request, spreadsheet_id : str, group_identifier : int):
    row_idx = group_identifier + 10
    photo_row_value_range = gen_sheets_range("Photo Trns", f"A{row_idx}", f"X{row_idx}")
    row = get_single_spreadsheet_range(spreadsheet_id, photo_row_value_range)
    
    # Since google sheets removes empty values, pad out values
    row += [""] * (24 - len(row))

    lp = row[7] + row[12] + row[17]
    hs = row[8] + row[13] + row[18]
    oshs = row[9]
    return Response(data={"message" : {
        "photo_type" : row[1],
        "dpi" : row[2],
        "lp" : lp if lp != "" else 0,
        "hs" : hs if hs != "" else 0,
        "oshs" : oshs if oshs != "" else 0,
        "custom_folder_name" : row[23]
    }})


@api_view(["GET"])
def photo_row(request, spreadsheet_id : str, group_identifier : str): 
    try:
        photo_row = PhotoRow()
        photo_row.pull_from_sheet(spreadsheet_id, group_identifier)
        return photo_row.to_response()
    
    except CustomException as custom_exception:
        return custom_exception.get_response()
    
    except Exception as e:
        return UnknownException(str(e)).get_response()
    

@api_view(["GET"])
def check_photo_row(request, spreadsheet_id : str, group_identifier : str):
    try:
        photo_row = PhotoRow()
        photo_row.pull_from_sheet(spreadsheet_id, group_identifier)

        slides_final_checker = photo_row.to_final_check_query(group_identifier)

        slides_final_checker.final_check()
        return Response(data={"message" : "All good!"})
        
    except CustomException as custom_exception:
        return custom_exception.get_response()
    
    except Exception as e:
        return UnknownException(str(e)).get_response()


@api_view(["GET"])
def check_all_photo_rows(request, spreadsheet_id : str):
    current_group = ""

    try:
        # First, get all group identifiers so we know how many groups long this is
        identifiers_request = SheetsRequest(spreadsheet_id, [RangeRequest("Photo Trns", "A11", "A")], False)
        identifiers_response = identifiers_request.execute()
        identifiers = identifiers_response.values[0]

        # Next, get the corrected column and every photo group
        ranges : RangeRequest = [RangeRequest("Photo Trns", f"D11", "D")]
        for i, _ in enumerate(identifiers):
            ranges.append(RangeRequest("Photo Trns", f"A{11 + i}", f"X{11 + i}"))
        all_groups_request = SheetsRequest(spreadsheet_id, ranges, True)
        all_groups_response = all_groups_request.execute()
        corrected_row = all_groups_response.values[0]

        # Initialize the first row to get the project name and stuff, i don't care if this is inefficient
        iterating_photo_row = PhotoRow(all_groups_response.values[1])
        iterating_photo_row.pull_from_sheet(spreadsheet_id, identifiers[0])

        # Final check every group
        for i, sheets_group_row in enumerate(all_groups_response.values[1:]):
            current_group = identifiers[i]
            iterating_photo_row.init_from_received_data(corrected_row, sheets_group_row)
            final_check_query : PhotoFinalCheckQuery = iterating_photo_row.to_final_check_query(identifiers[i])
            final_check_query.final_check()
            print(f"{current_group} is clear!")
        
        return Response(data={"message" : "All good!"})
    
    except CustomException as custom_exception:
        multi_group_custom_exception = MultiGroupCustomException(custom_exception)
        multi_group_custom_exception.group_identifier = current_group
        return multi_group_custom_exception.get_response()
    
    except Exception as e:
        multi_group_unknown_exception = MultiGroupUnknownException(custom_exception)
        multi_group_unknown_exception.group_identifier = current_group
        return multi_group_unknown_exception.get_response()
