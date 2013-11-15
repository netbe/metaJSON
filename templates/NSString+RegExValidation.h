//
//  NSString+RegExValidation.h
//
//  Created by MetaJSONParser.
//  Copyright (c) _YEAR_ SinnerSchrader Mobile. All rights reserved.

#import <Foundation/Foundation.h>

@interface NSString (RegExValidation)

- (NSUInteger) numberOfMatchesWithRegExString:(NSString *)regExString;

- (BOOL) matchesRegExString:(NSString *)regExString;

@end
