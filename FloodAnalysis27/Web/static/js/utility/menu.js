$( function(){
	
	$('.menu').click(function(){
		
		$('.menu').each(function(){
			$(this).removeClass('selected');
		})
		
		$(this).addClass('selected');
		
		id = $(this).attr('id');
		
		$(".content_div").slideUp();
		
		var scrollUp = 0;
	    $('html, body').animate({scrollTop:scrollUp}, 250);
		
		setTimeout(function(){
			$("#" + id + "_content").slideDown();
			
			setTimeout(function(){
				
					val = $("#" + id + "_content").css('height');
					val = parseFloat(val.substring(0, val.length - 2));
					console.log(val);
					
					if (val > 700){
						val2 = $("#" + id + "_content").css('margin-top');
						val2 = parseFloat(val2.substring(0, val2.length - 2));
						final_val = (val + (val2 * 2)) + 'px';
					} else {
						final_val = val + 'px';
					}
					
						
					$('#sidebar').css('height', final_val);
				
			}, 1000);
			
		}, 750);
		
		
	})
})