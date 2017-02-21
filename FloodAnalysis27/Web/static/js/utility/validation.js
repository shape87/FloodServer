$(function(){
	
	$.validator.addMethod(
	        "regex",
	        function(value, element, regexp) {
	            var re = new RegExp(regexp);
	            return this.optional(element) || re.test(value);
	        },
	        "Please check your input."
	);
	
	//Test form
	$("#query_nwis_form").validate({
		  rules: {
		    station_id: {
		    	required: true,
		    	digits: true
		    },
		    start_date: {
		    	required: true,
		    },
		    end_date: {
		    	required: true,
		    }
		  }
		});
	
	$("#geometry_input_form").validate({
		rules: {
			coord_file: {
				required: true
			},
			datum: {
				required: true,
				number: true
			},
	        properties_file: {
	        	required: function() {
	        		return $("#manual").is(":checked");
	        	}
	        },
	        z_step: {
	        	required: function() {
	        		return $("#auto").is(":checked");
	        	},
	        	number: true
	        },
	        sub_divisions: {
	        	regex: "^([0-9][,]?)+$"
	        }
		}
	})
	
	$("#manning_input_form").validate({
		rules: {
			channel_properties_file: {
	        	required: function() {
	        		return $("#table_manning").is(":checked");
	        	}
	        },
        
        	manning_coef: {
				required: function() {
	        		return $("#static_manning").is(":checked");
	        	},
				number: true
			},
		}
	})
	
	$("#flood_input_form").validate({
		rules: {
			channel_bed: {
				required: true,
				number: true
			},
			stage_hB: {
				required: true,
				number: true,
			},
			stage_hp: {
				required: true,
				number: true,
			},
			days_between: {
				required: true,
				number: true,
			},
			flow_QB: {
				required: true,
				number: true,
			},
			flow_Qp: {
				required: true,
				number: true,
			},
			flow_Q0: {
				required: true,
				number: true,
			}
		}
	})
	
	$('#process_newton').validate({
		rules: {
			manning_file: {
	        	required: function() {
	        		return $("#table_manning").is(":checked");
	        	}
	        },
        
        	manning_coef: {
				required: function() {
	        		return $("#static_manning").is(":checked");
	        	},
				number: true
			}
		}
	})
})