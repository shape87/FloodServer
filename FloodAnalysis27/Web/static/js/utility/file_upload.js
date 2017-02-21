$(function () {
	
	//set up jquery datetime picker for query nwis form
	$('#start_date').datetimepicker();
	$('#end_date').datetimepicker();
	
	//hide upload items if not 
	if($('#manual').is(":checked")){
		$('#manual_calc').show()
		$('#auto_calc').hide()
	} else{
		$('#auto').attr("checked", "checked")
		$('#auto_calc').show()
		$('#manual_calc').hide()
	}
	
	$('.properties_radio').change(function(){
		if($('#auto').is(":checked")){
			$('#manual_calc').hide()
			$('#auto_calc').show()
			$('#properties_file-error').remove();
			$('#properties_file').removeClass('error');
			
		} else{
			$('#manual_calc').show()
			$('#auto_calc').hide()
			$('#radio1').removeAttr("checked", "checked")
		}
	})
	
	//hide upload items if not 
	if($('#table_manning').is(":checked")){
		$('#table_calc').show()
		$('#static_calc').hide()
	} else{
		$('#static_manning').attr("checked", "checked")
		$('#static_calc').show()
		$('#table_calc').hide()
	}
	
	$('.manning_radio').change(function(){
		if($('#static_manning').is(":checked")){
			$('#table_calc').hide()
			$('#static_calc').show()
			$('#channel_properties_file-error').remove();
			$('#channel_properties_file').removeClass('error');
			
		} else{
			$('#table_calc').show()
			$('#static_calc').hide()
			$('#static_manning').removeAttr("checked", "checked")
		}
	})

	$('#query_nwis_form').submit(function(e){
		e.preventDefault();
		
		
		if($('#query_nwis_form').valid() == true){ 
			
			slide_loading_message('down');
			
			var formData = new FormData();
			formData.append('station_id', $('#station_id').val());
			formData.append('start_date', $('#start_date').val());
			formData.append('end_date', $('#end_date').val());
			formData.append('tz', $('#tz').val());
			formData.append('daylight_savings', $('#daylight_savings').val());
			
			$.ajax({
				type: 'POST',
				url: window.location.href + 'query_nwis',
				data: formData,
		        cache: false,
		        contentType: false,
		        processData: false,
				success: function(data){
					
					slide_success_message(data.message);
					
				},
				error: function(){
					
					slide_error_message("Could not query NWIS, check parameters and try again");
					
				}
			})
		}
	})
	
	$('#geometry_input_form').submit(function(e){
		e.preventDefault();
		
		
		if($('#geometry_input_form').valid() == true){ 
			
			slide_loading_message('down');
			
			var formData = new FormData();
			formData.append('coord_file', $('#coord_file')[0].files[0]);
			formData.append('datum', $('#datum').val());
			formData.append('sub_divisions', $('#sub_divisions').val());
			
			//If manual table upload
			if($('#manual').is(":checked")){
				formData.append('properties_file', $('#properties_file')[0].files[0]);
				formData.append('auto_calculate', 'false');
			}else{
				formData.append('z_step', $('#z_step').val())
				formData.append('auto_calculate', 'true');
			}
			
			$.ajax({
				type: 'POST',
				url: window.location.href + 'calculate_geometry',
				data: formData,
		         // Options to tell jQuery not to process data or worry about the content-type
		        cache: false,
		        contentType: false,
		        processData: false,
				success: function(data){
					
					slide_success_message(data.message);
					
					$('#table_download').show();
					$('#picture').empty();
					$('#picture').append('<img style="height: 400px; width: 550px; border: 1px solid black" src="image?name=cross&dummy=' + Math.random() + '" />')

				},
				error: function(){
					
					slide_error_message("Could not create table, check parameters and try again");
				
				}
			})
		}
	})
	
	$('#manning_input_form').submit(function(e){
		e.preventDefault();
		
		if($('#manning_input_form').valid() == true){ 
			
			slide_loading_message('down');
			
			var formData = new FormData();
			
			//If manual table upload
			if($('#table_manning').is(":checked")){
				formData.append('channel_properties_file', $('#channel_properties_file')[0].files[0]);
				formData.append('static_calculate', 'false');
			}else{
				formData.append('manning_coef', $('#manning_coef').val());
				formData.append('static_calculate', 'true');
			}
			
			$.ajax({
				type: 'POST',
				url: window.location.href + 'calculate_manning',
				data: formData,
				cache: false,
		        contentType: false,
		        processData: false,
				success: function(data){
					
					slide_success_message(data.message);
				
				},
				error: function(){
					
					slide_error_message("Could not calculate manning coefficient/s");
					
				}
			})
		}
	})
	
	$('#flood_input_form').submit(function(e){
		e.preventDefault();
		
		
		if($('#flood_input_form').valid() == true){ 
			
			slide_loading_message('down');
			
			var formData = new FormData();
			
			formData.append('channel_bed_slope', $('#channel_bed').val());
			formData.append('stage_hB', $('#stage_hB').val());
			formData.append('stage_hp', $('#stage_hp').val());
			formData.append('days_between', $('#days_between').val());
			formData.append('flow_QB', $('#flow_QB').val());
			formData.append('flow_Qp', $('#flow_Qp').val());
			formData.append('flow_Q0', $('#flow_Q0').val());
			
			$.ajax({
				type: 'POST',
				url: window.location.href + 'flood_parameters',
				data: formData,
		         // Options to tell jQuery not to process data or worry about the content-type
		        cache: false,
		        contentType: false,
		        processData: false,
				success: function(data){
					
					slide_success_message(data.message);
				
				},
				error: function(){
					
					slide_error_message("Could not create table, check parameters and try again");
				
				}
			})
		}
	})
	
	$('#process_newton').submit(function(e){ 
		e.preventDefault();
		
		if($('#process_newton').valid() == true){ 
			slide_loading_message('down');
			
			var formData = new FormData();
			
			//If manual table upload
			if($('#table_manning').is(":checked")){
				formData.append('manning_file', $('#manning_file')[0].files[0]);
				formData.append('static_calculate', 'false');
			}else{
				formData.append('manning_coef', $('#manning_coef').val());
				formData.append('static_calculate', 'true');
			}
			
			if($('#discrete_output').is(":checked")){
				formData.append('discrete_output', 'true');
			} else{
				formData.append('discrete_output', 'false');
			}
			
			if($('#alt_output').is(":checked")){
				formData.append('alt_output', 'true');
			} else{
				formData.append('alt_output', 'false');
			}
			
			$.ajax({
				type: 'POST',
				url: window.location.href + 'newton_raphson',
				data: formData,
				cache: false,
			    contentType: false,
			    processData: false,
				success: function(data){
					
					slide_success_message(data.message);
					
					$('#results').empty()
					$('#results').append('<p style="margin-left: 10px">SSR = ' + data.ssr + '</p>')
					$('#results').append('<img class="result_image" src="image?name=result1&dummy=' + Math.random() + '" />')
					$('#results').append('<img class="result_image" src="image?name=result2&dummy=' + Math.random() + '" />')
					$('#flow_table_download').show()
					
				},
				error: function(){
	
					$('#flow_table_download').hide()
					slide_error_message("Could not process newton raphson, check parameters and try again");
				}
			})
		}
	})
	
	var slide_success_message = function(message) {
		slide_loading_message('up');
		
		$('#success_message .message').text('');
		$('#success_message').slideDown();
		$('#success_message .message').text(message);
		
		setTimeout(function(){
			$('#success_message').slideUp();
		}, 5000)
		
	}
	
	var slide_error_message = function(message){
		slide_loading_message('up');
		
		$('#error_message .message').text('');
		$('#error_message').slideDown();
		$('#error_message .message').text(message);
		
		setTimeout(function(){
			$('#error_message').slideUp();
		}, 5000);
		
	}
	
	var slide_loading_message = function(dir){
		if (dir == 'down'){
			$('#loading_message').slideDown();
		} else {
			$('#loading_message').slideUp();
		}
	}
})
